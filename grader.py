"""Autograder mini project Tkinter: Konverter Suhu.

Menjalankan main.py praktikan dengan Tkinter tiruan (faketk.py), lalu
"mengetik" di Entry, "memilih" Radiobutton dan "mengklik" Button secara otomatis
dan memberi nilai per poin spesifikasi (total 100). Yang dinilai adalah perilaku
program, bukan tampilannya.

Dipakai di halaman web (Pyodide) dan bisa juga dijalankan langsung:

    python grader.py main.py
"""

import builtins
import io
import json
import re
import sys
import time

import faketk

LINE_LIMIT = 400_000       # batas baris dieksekusi per langkah (cegah infinite loop)
NAMA_BERKAS = "main.py"


# ---------------------------------------------------------------- penghenti
class _Stop(BaseException):
    """Dipakai grader untuk menghentikan program praktikan."""


class LoopTerlalu(_Stop):
    pass


# Sekali grader memutuskan berhenti, setiap baris berikutnya ikut melempar
# sentinel ini, jadi `except:` polos milik praktikan tidak bisa menelannya.
_HENTIKAN = [None]


def _hentikan(exc):
    _HENTIKAN[0] = exc
    raise exc


def _tolak_input(*args, **kwargs):
    raise EOFError("input() tidak bisa dipakai di tugas GUI ini")


class _Tangkap(io.TextIOBase):
    def __init__(self):
        self.isi = ""

    def write(self, s):
        if _HENTIKAN[0] is not None:
            raise _HENTIKAN[0]
        self.isi += s
        return len(s)


def _jalankan(fn, tangkap):
    """Menjalankan fn dengan batas baris. Mengembalikan (status, pesan)."""
    hitung = [0]
    _HENTIKAN[0] = None

    def tracer(frame, event, arg):
        if _HENTIKAN[0] is not None:
            raise _HENTIKAN[0]
        if event == "line":
            hitung[0] += 1
            if hitung[0] > LINE_LIMIT:
                _hentikan(LoopTerlalu())
        return tracer

    stdout_asli, sleep_asli, input_asli = sys.stdout, time.sleep, builtins.input
    sys.stdout = tangkap
    time.sleep = lambda *_a, **_k: None
    builtins.input = _tolak_input
    sys.settrace(tracer)
    try:
        fn()
        return "ok", ""
    except SystemExit:
        return "ok", ""
    except LoopTerlalu:
        return "loop", "Program berjalan terlalu lama tanpa selesai (kemungkinan infinite loop, mis. while True di luar mainloop)."
    except _Stop as e:
        return "loop", str(e)
    except BaseException as e:      # crash milik program praktikan
        pesan = faketk._ringkas_error(e)
        return "crash", pesan
    finally:
        sys.settrace(None)
        _HENTIKAN[0] = None
        sys.stdout = stdout_asli
        time.sleep = sleep_asli
        builtins.input = input_asli


# ---------------------------------------------------------------- satu sesi program
TOMBOL_BUKAN = re.compile(r"keluar|exit|quit|tutup|close|reset|hapus|clear|bersih|batal|cancel", re.I)
TOMBOL_KONVERSI = re.compile(r"konversi|hitung|convert|ubah|proses|submit|\bok\b|tampil|cek", re.I)
_ANGKA = re.compile(r"(?<!\d)-?\d+(?:[.,]\d+)?")


def angka_dalam(teks):
    out = []
    for m in _ANGKA.finditer(str(teks).replace("−", "-")):
        try:
            out.append(float(m.group().replace(",", ".")))
        except ValueError:
            pass
    return out


def ada_angka(daftar_teks, target, tol=0.06):
    return any(abs(x - target) <= tol for t in daftar_teks for x in angka_dalam(t))


def hampir_angka(daftar_teks, target):
    return any(abs(x - target) <= 0.51 for t in daftar_teks for x in angka_dalam(t))


def arah_dari_teks(teks):
    s = str(teks).lower().replace("°", " ").replace("º", " ")
    c = re.search(r"celsius|\bc\b", s)
    f = re.search(r"fahrenheit|\bf\b", s)
    if c and f:
        return "CF" if c.start() < f.start() else "FC"
    kata_tujuan = r"\b(ke|to|jadi|menjadi)\b|→|->|=>"
    if c:
        return "FC" if re.search(kata_tujuan, s[:c.start()]) else "CF"
    if f:
        return "CF" if re.search(kata_tujuan, s[:f.start()]) else "FC"
    return None


def _potong(t, n=40):
    t = str(t).replace("\n", " ⏎ ")
    return t if len(t) <= n else t[: n - 1] + "…"


class Sesi:
    """Satu kali menjalankan program praktikan dari awal, plus aksi 'user'."""

    def __init__(self, src):
        self.log = []
        self.status = "ok"
        self.pesan = ""
        self.tangkap = _Tangkap()
        faketk.reset()
        faketk.install()
        try:
            kode = compile(src, NAMA_BERKAS, "exec")
        except SyntaxError as e:
            self.status, self.pesan = "crash", f"SyntaxError: {e.msg} (baris {e.lineno})"
            return
        ns = {"__name__": "__main__", "__file__": NAMA_BERKAS}
        self.status, self.pesan = _jalankan(lambda: exec(kode, ns), self.tangkap)
        self.catat("Program dijalankan" + ("" if self.status == "ok" else f" → BERHENTI: {self.pesan}"))
        if self.tangkap.isi.strip():
            self.catat("print(): " + _potong(self.tangkap.isi.strip(), 120))

    def catat(self, baris):
        self.log.append(baris)

    def transkrip(self, dengan_pohon=False):
        out = list(self.log)
        if dengan_pohon:
            out.append("")
            out.append("Susunan widget:")
            out.append(faketk.pohon() or "(tidak ada jendela)")
        return "\n".join(out)

    # ---- mencari widget berdasarkan peran, bukan nama variabel
    def widgets(self, kelas):
        return [w for w in faketk.semua_widget() if isinstance(w, kelas)]

    def entry_input(self):
        es = [w for w in self.widgets(faketk.Entry) if type(w).__name__ not in ("Spinbox", "Combobox")]
        return es[0] if es else None

    def tombol(self):
        bs = self.widgets(faketk.Button)
        pilih = [b for b in bs if TOMBOL_KONVERSI.search(b.teks() or "")]
        if pilih:
            return pilih[0]
        sisa = [b for b in bs if not TOMBOL_BUKAN.search(b.teks() or "")]
        return sisa[0] if sisa else None

    def kelompok_radio(self):
        """Mengembalikan (dict arah->Radiobutton, catatan). Kosong kalau tidak ada Radiobutton."""
        rs = self.widgets(faketk.Radiobutton)
        grup = {}
        for r in rs:
            grup.setdefault(id(r._opts.get("variable")), []).append(r)
        if not grup:
            return {}, ""
        anggota = max(grup.values(), key=len)
        if len(anggota) < 2:
            return {}, ""
        peta = {}
        for r in anggota:
            a = arah_dari_teks(r.teks())
            if a and a not in peta:
                peta[a] = r
        if len(peta) == 2:
            return peta, ""
        return {"CF": anggota[0], "FC": anggota[1]}, "Teks Radiobutton tidak jelas, dianggap urutan: Celsius→Fahrenheit lalu Fahrenheit→Celsius"

    # ---- aksi user
    def _aksi(self, fn):
        status, pesan = _jalankan(fn, self.tangkap)
        if status != "ok":
            self.catat(f"(!) {pesan}")
        return status

    def ketik(self, entry, teks):
        ok, cat = faketk.ketik(entry, teks)
        self.catat(f'Entry diisi: "{teks}"' if ok else f"(!) {cat}")
        return ok, cat

    def pilih_radio(self, radio):
        self._aksi(radio.invoke)
        self.catat(f'Radiobutton dipilih: "{_potong(radio.teks())}"')

    def snapshot(self):
        masuk = (faketk.Label, faketk.Text, faketk.Entry, faketk.Message)
        ent = self.entry_input()
        out = {}
        for w in faketk.semua_widget():
            if isinstance(w, masuk) and w is not ent and type(w).__name__ not in ("Combobox", "Spinbox"):
                t = w.teks()
                if t is not None:
                    out[id(w)] = (w, t)
        return out

    def klik(self, tombol):
        n_dialog = len(faketk.STATE.dialogs)
        n_err = len(faketk.STATE.callback_errors)
        sebelum = self.snapshot()
        self._aksi(tombol.invoke)
        self.catat(f'Tombol diklik: "{_potong(tombol.teks())}"')
        return self._laporan(sebelum, n_dialog, n_err)

    def tekan_enter(self, entry):
        n_dialog = len(faketk.STATE.dialogs)
        n_err = len(faketk.STATE.callback_errors)
        sebelum = self.snapshot()
        jumlah = [0]
        self._aksi(lambda: jumlah.__setitem__(0, faketk.fire(entry, "<Return>", keysym="Return", char="\r", keycode=13)))
        self.catat(f"Tombol Enter ditekan di Entry ({jumlah[0]} handler bind dipanggil)")
        lap = self._laporan(sebelum, n_dialog, n_err)
        lap["jumlah_handler"] = jumlah[0]
        return lap

    def _laporan(self, sebelum, n_dialog, n_err):
        sesudah = self.snapshot()
        terlihat, tersembunyi = [], []
        for k, (w, t) in sesudah.items():
            if k not in sebelum or sebelum[k][1] != t:
                if t.strip():
                    (terlihat if faketk.terlihat(w) else tersembunyi).append(t)
                    self.catat(f'Label/teks berubah: "{_potong(t)}"' + ("" if faketk.terlihat(w) else "   (widget ini belum di-layout, tidak tampil)"))
        dialog = faketk.STATE.dialogs[n_dialog:]
        for d in dialog:
            self.catat(f'Dialog: {d["jenis"]}("{_potong(d["judul"] or "")}", "{_potong(d["pesan"] or "")}")')
        errors = faketk.STATE.callback_errors[n_err:]
        for e in errors:
            self.catat(f"(!) Error di dalam command: {e}")
        return {"terlihat": terlihat, "tersembunyi": tersembunyi, "dialog": dialog, "errors": errors}


# ---------------------------------------------------------------- pemeriksaan per poin
def _hasil(kode, judul, bobot, skor, catatan, transkrip=""):
    skor = max(0, min(bobot, round(skor)))
    return {"kode": kode, "judul": judul, "bobot": bobot, "skor": skor,
            "catatan": "; ".join(c for c in catatan if c), "transkrip": transkrip}


def _kalimat_error_crash(s):
    if s.status == "ok":
        return ""
    if s.status == "loop":
        return _potong(s.pesan, 150)
    return f"Program berhenti karena error: {_potong(s.pesan, 150)}"


def uji_jendela(src, dasar):
    s = dasar
    root = faketk.STATE.default_root
    skor, cat = 0, [_kalimat_error_crash(s)]
    if root is not None:
        skor += 4
        cat.append("Tk() dibuat ✓")
        if root._title_set and root._title.strip() and root._title.strip().lower() != "tk":
            if "suhu" in root._title.lower():
                skor += 4
                cat.append(f'Judul jendela "{_potong(root._title, 30)}" ✓')
            else:
                skor += 2
                cat.append('Judul jendela belum sesuai, seharusnya memuat "Konverter Suhu"')
        else:
            cat.append("title() belum dipanggil")
        if root._geometry_set and re.match(r"^\d+x\d+", root._geometry or ""):
            skor += 3
            cat.append(f"geometry({root._geometry!r}) ✓")
        elif root._geometry_set:
            skor += 1
            cat.append("geometry() dipanggil tapi formatnya salah, contoh yang benar: \"320x260\"")
        else:
            cat.append("geometry() belum dipanggil")
    else:
        cat.append("Tidak ada jendela: pakai root = tk.Tk()")
    if faketk.STATE.mainloop > 0:
        skor += 4
        cat.append("mainloop() dipanggil ✓")
    else:
        cat.append("mainloop() belum dipanggil, jendela tidak akan tampil")
    return _hasil("T1", "Jendela: Tk(), title(), geometry(), dan mainloop()", 15, skor, cat, s.transkrip(dengan_pohon=True))


def uji_widget(src, dasar):
    s = dasar
    skor, cat = 0, []
    n_entry = len(s.widgets(faketk.Entry))
    n_btn = len(s.widgets(faketk.Button))
    n_lbl = len(s.widgets(faketk.Label))
    if n_entry >= 1:
        skor += 3
        cat.append("Entry ✓")
    else:
        cat.append("Belum ada Entry untuk mengetik suhu")
    if n_btn >= 1:
        skor += 3
        cat.append("Button ✓")
    else:
        cat.append("Belum ada Button")
    if n_lbl >= 2:
        skor += 3
        cat.append(f"{n_lbl} Label ✓")
    elif n_lbl == 1:
        skor += 1
        cat.append("Baru 1 Label: tambahkan Label judul/keterangan selain Label hasil")
    else:
        cat.append("Belum ada Label")
    rs = s.widgets(faketk.Radiobutton)
    grup = {}
    for r in rs:
        grup.setdefault(id(r._opts.get("variable")), []).append(r)
    terbaik = max(grup.values(), key=len) if grup else []
    nilai_berbeda = {str(r._opts.get("value", "")) for r in terbaik}
    if len(terbaik) >= 2 and len(nilai_berbeda) >= 2:
        skor += 4
        cat.append(f"{len(terbaik)} Radiobutton satu kelompok ✓")
        if not any(getattr(r, "_var_bawaan", False) for r in terbaik):
            skor += 2
            cat.append("Radiobutton memakai variabel Tkinter (StringVar/IntVar) ✓")
        else:
            cat.append("Radiobutton tidak diberi variable=, buat StringVar/IntVar")
    elif len(rs) >= 2:
        skor += 1
        cat.append("Radiobutton harus memakai satu variable yang sama dan value yang berbeda")
    elif len(rs) == 1:
        cat.append("Baru 1 Radiobutton, perlu 2: Celsius ke Fahrenheit dan Fahrenheit ke Celsius")
    else:
        cat.append("Belum ada Radiobutton untuk memilih arah konversi")
    return _hasil("T2", "Widget lengkap: Label, Entry, 2 Radiobutton satu variabel, Button", 15, skor, cat, s.transkrip(dengan_pohon=True))


def uji_layout(src, dasar):
    s = dasar
    skor, cat = 0, []
    kandidat = [w for w in faketk.semua_widget() if not isinstance(w, (faketk.Menu, faketk.Toplevel))]
    if s.status == "crash" and "geometry manager" in s.pesan:
        cat.append("pack() dan grid() dicampur dalam satu wadah: " + _potong(s.pesan, 140))
        cat.append("Pilih satu: pakai semua pack atau semua grid di wadah yang sama")
    elif len(kandidat) >= 3:
        skor += 4
        cat.append("Tidak ada pack dan grid yang bertabrakan ✓")
    if len(kandidat) < 3:
        cat.append("Widget belum cukup banyak untuk menilai layout")
    else:
        tidak = [w for w in kandidat if not faketk.terlihat(w)]
        skor += 6 * (len(kandidat) - len(tidak)) / len(kandidat)
        if not tidak:
            cat.append(f"Semua {len(kandidat)} widget sudah di-pack/grid/place ✓")
        else:
            nama = ", ".join(f"{type(w).__name__} \"{_potong(w.teks() or '', 14)}\"".replace(' ""', "") for w in tidak[:4])
            cat.append(f"{len(tidak)} widget belum di-pack/grid/place sehingga tidak tampil: {nama}")
            cat.append("Ingat: widget = Label(...).pack() menyimpan None, tulis pack() di baris terpisah")
    return _hasil("T3", "Layout manager: semua widget tampil, pack dan grid tidak bertabrakan", 10, skor, cat, s.transkrip(dengan_pohon=True))


def _siapkan_konversi(src, arah, teks_input):
    """Menjalankan program baru, memilih arah, mengisi Entry. Mengembalikan (sesi, entry, tombol, catatan_gagal)."""
    s = Sesi(src)
    e, b = s.entry_input(), s.tombol()
    if e is None:
        return s, e, b, "Tidak ada Entry untuk mengetik suhu"
    if b is None:
        return s, e, b, "Tidak ada Button untuk memicu konversi"
    radio, cat_radio = s.kelompok_radio()
    if radio:
        s.pilih_radio(radio[arah])
    else:
        s.catat("(!) Radiobutton tidak ditemukan, arah konversi tidak bisa dipilih")
    ok, cat = s.ketik(e, teks_input)
    if not ok:
        return s, e, b, cat
    return s, e, b, ""


def _nilai_hasil(lap, target):
    """Mengembalikan (pecahan nilai, catatan)."""
    if ada_angka(lap["terlihat"], target):
        return 1.0, "✓"
    if hampir_angka(lap["terlihat"], target):
        return 0.5, "dibulatkan ke bilangan bulat, tampilkan 1 angka desimal"
    if ada_angka(lap["tersembunyi"], target):
        return 0.5, "hasil benar tapi Label hasil belum di-pack/grid/place"
    pesan_dialog = [d["pesan"] or "" for d in lap["dialog"]]
    if ada_angka(pesan_dialog, target):
        return 0.5, "hasil tampil di messagebox, seharusnya di Label"
    return 0.0, ""


def _satu_konversi(src, arah, teks_input, target, nama_arah):
    s, e, b, gagal = _siapkan_konversi(src, arah, teks_input)
    awal = f'{teks_input} {nama_arah}'
    if gagal:
        return 0.0, f"{awal}: {gagal}", s
    lap = s.klik(b)
    frac, cat = _nilai_hasil(lap, target)
    if frac == 1.0:
        return 1.0, f"{awal} → {target:g} ✓", s
    if frac > 0:
        return frac, f"{awal} → {cat}", s
    if lap["errors"]:
        return 0.0, f"{awal}: error di tombol: {_potong(lap['errors'][0], 110)}", s
    ada = lap["terlihat"][:1]
    return 0.0, f"{awal}: seharusnya {target:g}" + (f", Label berisi \"{_potong(ada[0], 30)}\"" if ada else ", tidak ada Label yang berubah"), s


def uji_konversi(src, kode, judul, bobot, arah, kasus, nama_arah):
    skor, cat, jejak = 0.0, [], []
    per_kasus = bobot / len(kasus)
    for teks, target in kasus:
        frac, c, s = _satu_konversi(src, arah, teks, target, nama_arah)
        skor += per_kasus * frac
        cat.append(c)
        jejak.append(s.transkrip())
    return _hasil(kode, judul, bobot, skor, cat, "\n\n".join(jejak))


def uji_error(src):
    skor, cat, jejak = 0.0, [], []
    for teks, nama, w_dialog, w_jenis in (("abc", "input abc", 5, 3), ("", "input kosong", 4, 3)):
        s, e, b, gagal = _siapkan_konversi(src, "CF", teks)
        if gagal:
            cat.append(f"{nama}: {gagal}")
            jejak.append(s.transkrip())
            continue
        lap = s.klik(b)
        jejak.append(s.transkrip())
        if lap["dialog"]:
            jenis = lap["dialog"][0]["jenis"]
            skor += w_dialog
            if jenis in ("showerror", "showwarning"):
                skor += w_jenis
                cat.append(f"{nama} → {jenis} ✓")
            else:
                cat.append(f"{nama} → pakai showerror atau showwarning, bukan {jenis}")
        elif lap["errors"]:
            cat.append(f"{nama}: error di tombol: {_potong(lap['errors'][0], 100)}")
            cat.append("Bungkus konversi dengan try/except ValueError lalu tampilkan messagebox.showerror")
        elif lap["terlihat"]:
            skor += 1
            cat.append(f"{nama}: pesan error tampil di Label, seharusnya messagebox.showerror")
        else:
            cat.append(f"{nama}: tidak ada pesan error sama sekali")
    return _hasil("T6", "Input salah (huruf atau kosong) ditangani dengan messagebox", 15, skor, cat, "\n\n".join(jejak))


def uji_enter(src):
    s, e, b, gagal = _siapkan_konversi(src, "CF", "100")
    if gagal:
        return _hasil("T7", "Event: tekan Enter di Entry memicu konversi (bind)", 10, 0, [gagal], s.transkrip())
    lap = s.tekan_enter(e)
    skor, cat = 0, []
    # pembanding: hasil klik tombol dengan masukan yang sama (poin ini menilai bind, bukan rumus)
    s2, e2, b2, gagal2 = _siapkan_konversi(src, "CF", "100")
    lap_klik = s2.klik(b2) if not gagal2 else {"terlihat": []}
    if lap["jumlah_handler"] > 0:
        skor += 4
        cat.append('bind("<Return>") ditemukan ✓')
        if lap["terlihat"] and (lap["terlihat"] == lap_klik["terlihat"] or ada_angka(lap["terlihat"], 212)):
            skor += 6
            cat.append("Enter memicu konversi seperti tombol ✓")
        elif lap["errors"]:
            cat.append(f"Handler error: {_potong(lap['errors'][0], 110)}")
            cat.append("Handler bind menerima 1 argumen (event): def konversi(event=None)")
        else:
            cat.append("Enter tidak menghasilkan konversi seperti tombol")
    else:
        cat.append('Belum ada bind("<Return>", ...) pada Entry atau jendela')
    return _hasil("T7", "Event: tekan Enter di Entry memicu konversi (bind)", 10, skor, cat, s.transkrip())


# ---------------------------------------------------------------- titik masuk
JUDUL = {
    "T4": "Konversi Celsius ke Fahrenheit benar (100 dan 37)",
    "T5": "Konversi Fahrenheit ke Celsius benar (98.6 dan 50)",
}


def nilai_pengujian(file_main):
    """file_main: isi main.py (str). Mengembalikan dict hasil penilaian."""
    dasar = Sesi(file_main)
    hasil = [
        uji_jendela(file_main, dasar),
        uji_widget(file_main, dasar),
        uji_layout(file_main, dasar),
        uji_konversi(file_main, "T4", JUDUL["T4"], 20, "CF", [("100", 212.0), ("37", 98.6)], "°C"),
        uji_konversi(file_main, "T5", JUDUL["T5"], 15, "FC", [("98.6", 37.0), ("50", 10.0)], "°F"),
        uji_error(file_main),
        uji_enter(file_main),
    ]
    faketk.reset()
    return {"total": sum(h["skor"] for h in hasil), "tes": hasil, "kurs_uji": None}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        r = nilai_pengujian(f.read())
    for t in r["tes"]:
        print(f"{t['kode']} {t['skor']:>2}/{t['bobot']}  {t['catatan']}")
    print("TOTAL", r["total"])
    if "-v" in sys.argv:
        for t in r["tes"]:
            print(f"\n===== {t['kode']} transkrip =====\n{t['transkrip']}")
