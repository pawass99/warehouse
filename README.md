# Dashboard Analitik Efektivitas Jumlah Developer

Project ini adalah dashboard Streamlit untuk menganalisis apakah jumlah developer pada project software sudah efektif, masih kurang, atau terlalu banyak. Data yang digunakan pada versi awal adalah dataset simulasi aktivitas repository software engineering, lalu dimasukkan ke SQLite agar dashboard membaca data melalui query SQL.

## Fitur Dashboard

- Filter slice dan dice berdasarkan tanggal, project size, project name, team, repository, dan developer.
- KPI cards untuk total project, developer, commits, pull requests, merge conflicts, productivity per developer, dan conflict rate.
- Bar chart: `Productivity per Developer by Project`.
- Scatter plot: `Developer Count vs Total Productivity`.
- Line chart: `Monthly Productivity Trend`.
- Donut chart: `Repository Activity Distribution`.
- Tabel agregasi per project dengan recommendation sederhana untuk membantu keputusan engineering manager.
- `Live GitHub Commit Activity` untuk melihat commit terbaru dari satu repository GitHub menggunakan GitHub REST API.

## Struktur Project

```text
.
|-- app.py
|-- data/
|   `-- repository_activity.csv
|-- database/
|   `-- repository_analytics.db
|-- scripts/
|   `-- seed_database.py
|-- pyproject.toml
|-- uv.lock
`-- README.md
```

## Cara Menjalankan dengan uv

Jika project dibuat dari awal:

```bash
uv init
uv add streamlit pandas plotly requests
```

Untuk project ini, dependency sudah ada di `pyproject.toml`, jadi cukup jalankan:

```bash
uv sync
uv run python scripts/seed_database.py
uv run streamlit run app.py
```

Dashboard akan tersedia di URL yang ditampilkan Streamlit, biasanya:

```text
http://localhost:8501
```

## Seed Database

Script seed akan membuat ulang dataset dan database:

```bash
uv run python scripts/seed_database.py
```

Script ini akan:

- Membuat folder `data/` dan `database/` jika belum ada.
- Generate dataset simulasi ke `data/repository_activity.csv`.
- Membuat database SQLite di `database/repository_analytics.db`.
- Drop dan replace tabel `repository_activity`, sehingga aman dijalankan ulang.

## Dataset

Dataset simulasi berisi aktivitas beberapa project software selama beberapa bulan. Kolom utamanya:

- `date`
- `month`
- `project_name`
- `project_size`
- `team_name`
- `developer_name`
- `developer_count`
- `repository_name`
- `commits`
- `pull_requests`
- `merge_conflicts`
- `issues_resolved`
- `bugs_reported`
- `lines_added`
- `lines_deleted`

Data dibuat agar realistis:

- Project kecil memiliki developer lebih sedikit.
- Project besar memiliki developer lebih banyak dan kompleksitas lebih tinggi.
- Project yang terlalu banyak developer cenderung memiliki merge conflict lebih tinggi.
- Project yang kekurangan developer dapat memiliki produktivitas lebih rendah.
- Aktivitas dibuat lintas bulan agar tren bisa divisualisasikan.

## Rumus Metrik

```text
total_activity = commits + pull_requests + issues_resolved
productivity_per_developer = total_activity / developer_count
conflict_rate = merge_conflicts / pull_requests
bug_rate = bugs_reported / commits
```

Pembagian dengan nol ditangani menggunakan `NULLIF` dan `COALESCE` pada query SQL.

## Visualisasi

- **Productivity per Developer by Project**: membandingkan efisiensi project berdasarkan aktivitas per developer.
- **Developer Count vs Total Productivity**: melihat hubungan jumlah developer dengan total produktivitas dan potensi conflict.
- **Monthly Productivity Trend**: melihat tren commit, pull request, issue resolved, dan total activity dari waktu ke waktu.
- **Repository Activity Distribution**: melihat proporsi aktivitas antar repository.
- **Project Effectiveness Summary**: tabel agregasi lengkap dengan rekomendasi efektivitas tim.

## Live GitHub Commit Activity

Dashboard memiliki fitur bonus untuk mengambil commit terbaru dari satu repository GitHub menggunakan endpoint:

```text
https://api.github.com/repos/{owner}/{repo}/commits
```

Cara pakai:

1. Jalankan dashboard.
2. Buka section `Live GitHub Commit Activity`.
3. Isi `GitHub owner`, `Repository name`, dan jumlah commit yang ingin ditampilkan.
4. Klik `Refresh Commit Data` jika ingin mengambil data terbaru.

Secara default, form memakai:

- `GITHUB_OWNER` dari environment variable jika tersedia, jika tidak memakai `pawas`.
- `GITHUB_REPO` dari environment variable jika tersedia, jika tidak memakai nama folder project.

Untuk public repository, token tidak wajib. Untuk private repository atau rate limit lebih longgar, set `GITHUB_TOKEN` sebelum menjalankan Streamlit:

```bash
export GITHUB_TOKEN="github_pat_your_token"
export GITHUB_OWNER="username-github-kamu"
export GITHUB_REPO="nama-repository-kamu"
uv run streamlit run app.py
```

Fitur ini menggunakan `st.cache_data` dengan TTL 60 detik. Artinya data bersifat **near real-time refresh**, bukan streaming WebSocket. Dashboard hanya mengambil commit terbaru dari satu repository; pull request, issue, dan banyak repository belum diintegrasikan.

## Catatan Pengembangan Berikutnya

Versi berikutnya dapat menambahkan analisis pull request, issue, banyak repository, atau sinkronisasi aktivitas GitHub ke SQLite agar histori live dapat dibandingkan dengan dataset analitik utama.
