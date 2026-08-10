# Dashboard Analisis Pasar Kerja Data Analyst AS

Dashboard interaktif berbasis **Streamlit** untuk menganalisis karakteristik pasar kerja **Data Analyst di Amerika Serikat (AS)** berdasarkan data lowongan pekerjaan dari tahun 2020–2025.

Dashboard ini berfokus pada analisis **kualifikasi pendidikan, kebutuhan hard skill dan soft skill, tingkat senioritas, pengalaman kerja, lokasi lowongan, perusahaan, serta struktur deskripsi pekerjaan**.

Link Dashboard: https://dashboard-lowongan-data-analyst-as.streamlit.app/

## Fitur Utama

Dashboard menyediakan beberapa fitur analisis yang dapat digunakan secara interaktif:

1. Filter Data

Pengguna dapat melakukan penyaringan data berdasarkan:

* Tahun publikasi lowongan
* Tingkat senioritas
* Lokasi / negara bagian
* Rentang pengalaman kerja
* Penyertaan lowongan dengan pengalaman yang tidak dinyatakan

Seluruh visualisasi dan KPI akan diperbarui berdasarkan filter yang dipilih.

2. Ringkasan Data

Menampilkan gambaran umum pasar kerja Data Analyst

3. Analisis Kualifikasi Pendidikan

Menganalisis persyaratan pendidikan yang tercantum dalam lowongan

4. Analisis Keterampilan

Menganalisis keterampilan hard skill maupun soft skill umum yang paling banyak dicari oleh perusahaan.

5. Analisis Struktur Deskripsi Pekerjaan

Menganalisis karakteristik teks pada deskripsi lowongan

6. Eksplorasi Data

Menyediakan tabel interaktif untuk mengeksplorasi data lowongan berdasarkan filter yang aktif.


## Normalisasi Perbandingan Antar Tahun

Jumlah lowongan yang tersedia pada setiap tahun tidak selalu sama. Oleh karena itu, perbandingan tren antar tahun tidak hanya menggunakan jumlah absolut.

Untuk analisis tren pendidikan dan keterampilan, digunakan **persentase / proporsi yang dinormalisasi terhadap total lowongan pada masing-masing tahun**.

Rumus yang digunakan:

```text
Persentase = (Jumlah lowongan yang mencantumkan kategori / Total lowongan pada tahun tersebut) × 100%
```

Pendekatan ini digunakan agar perubahan proporsi suatu kategori dapat dibandingkan secara lebih adil antar tahun meskipun jumlah sampel lowongan berbeda.

Contohnya, jika terdapat 1.000 lowongan pada tahun tertentu dan 300 di antaranya mencantumkan SQL:

```text
(300 / 1.000) × 100% = 30%
```

Dengan demikian, visualisasi tren menunjukkan **proporsi lowongan yang mencantumkan suatu kategori**, bukan sekadar perubahan jumlah lowongan absolut.

> Catatan: Satu lowongan dapat mencantumkan lebih dari satu pendidikan, jurusan, hard skill, atau soft skill. Oleh karena itu, persentase kategori tidak selalu berjumlah 100%.

## Dataset

Dashboard menggunakan gabungan dataset dari Kaggle yaitu:

*   Lowongan 2020: https://www.kaggle.com/datasets/andrewmvd/data-analyst-jobs
*   Lowongan 2022 & 2023: https://www.kaggle.com/datasets/simonebaldi/data-analyst-jobs-posting
*   Lowongan 2024: https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024
*   Lowongan 2025:https://www.kaggle.com/datasets/joykimaiyo18/linkedin-data-jobs-dataset

Data tersebut kemudian diolah sehingga menghasilkan informasi sebagai berikut:

| Kolom           | Deskripsi                                |
| --------------- | ---------------------------------------- |
| `posisi`        | Posisi pekerjaan                         |
| `perusahaan`    | Nama perusahaan                          |
| `lokasi`        | Lokasi / negara bagian                   |
| `pendidikan`    | Tingkat pendidikan yang disyaratkan      |
| `jurusan`       | Bidang studi / jurusan                   |
| `pengalaman`    | Minimal pengalaman kerja dalam tahun     |
| `level`         | Tingkat senioritas posisi                |
| `hard_skill`    | Keterampilan teknis yang dibutuhkan      |
| `soft_skill`    | Keterampilan interpersonal / profesional |
| `deskripsi`     | Deskripsi lengkap lowongan               |
| `deskripsi_len` | Panjang deskripsi dalam karakter         |
| `tahun`         | Tahun publikasi lowongan                 |

Nilai pengalaman yang tidak dapat ditentukan dari deskripsi disimpan sebagai:

```text
-1
```

Sedangkan informasi kategorikal yang tidak tersedia direpresentasikan sebagai:

```text
Unspecified
```

## Teknologi yang Digunakan

* **Python**
* **Streamlit** — pengembangan dashboard interaktif
* **Pandas** — pengolahan dan analisis data
* **Plotly Express** — visualisasi data

## Data Processing

Data lowongan dikumpulkan dari beberapa dataset untuk periode **2020–2025**, kemudian diproses melalui beberapa tahap:

```text
Data Gathering
      ↓
Data Cleaning & Filtering
      ↓
Data Merging
      ↓
Text Preprocessing
      ↓
Information Extraction
      ↓
Data Normalization
      ↓
Dashboard Visualization
```


## Instalasi

Clone repository:

```bash
git clone <URL_REPOSITORY>
cd <NAMA_REPOSITORY>
```

Buat virtual environment:

```bash
python -m venv venv
```

Aktifkan virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Menjalankan Dashboard (Lokal)

Jalankan aplikasi dengan:

```bash
streamlit run app.py
```

Dashboard kemudian dapat diakses melalui alamat lokal yang diberikan oleh Streamlit.

## Tujuan Analisis

Dashboard ini dikembangkan untuk memberikan gambaran mengenai **dinamika pasar kerja Data Analyst di Amerika Serikat**, khususnya dalam melihat:

* Perubahan kebutuhan tenaga kerja dari tahun ke tahun
* Persyaratan tingkat pendidikan
* Bidang studi yang banyak dicari
* Hard skill dan soft skill yang paling dibutuhkan
* Perbedaan kebutuhan berdasarkan tingkat senioritas
* Distribusi lowongan berdasarkan lokasi
* Perusahaan dengan aktivitas rekrutmen tertinggi
* Karakteristik dan kelengkapan deskripsi pekerjaan

## Catatan

Dashboard menampilkan data lowongan pekerjaan terbatas yang diambil hanya dari Kaggle dan **tidak merepresentasikan keseluruhan pasar kerja Data Analyst di Amerika Serikat**.
