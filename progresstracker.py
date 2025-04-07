"""
Modular Progress Tracker dengan Logging (Dioptimalkan untuk AI)
==============================================================

Skrip ini menggabungkan berbagai fungsi utilitas untuk analisis file, pembuatan grafik,
dan pembuatan laporan progress dalam satu file yang terstruktur dan modular, dengan penambahan logging.
Laporan ini dioptimalkan untuk diproses oleh model AI.
"""

import os
import time
import datetime
import json
import re
import hashlib
import difflib
from pathlib import Path
from collections import defaultdict, Counter
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import fnmatch
import logging
import gitignore_parser  # Tambahkan import untuk gitignore_parser

# Coba impor radon, jika tidak ada, setel ke None
try:
    import radon.raw
    import radon.complexity
except ImportError:
    print("Warning: radon library not found. Code complexity analysis will be disabled.")
    radon = None

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# =============================================================================
# Section 1: File Utilities
# =============================================================================

def get_file_hash(file_path, block_size=65536):
    """Hitung hash MD5 dari sebuah file menggunakan pendekatan berbasis blok."""
    logging.info(f"Memulai perhitungan hash untuk file: {file_path}")
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b""):
                hash_md5.update(block)
        file_hash = hash_md5.hexdigest()
        logging.info(f"Hash berhasil dihitung: {file_hash}")
        return file_hash
    except FileNotFoundError:
        logging.error(f"File tidak ditemukan: {file_path}")
        return None
    except PermissionError:
        logging.error(f"Izin ditolak saat membaca: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Gagal menghitung hash untuk {file_path}: {str(e)}")
        return None

def get_file_type(filename):
    """Menentukan tipe file berdasarkan ekstensi."""
    logging.info(f"Menentukan tipe file untuk: {filename}")
    ext = os.path.splitext(filename)[1].lower()
    categories = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.md': 'Markdown',
        '.json': 'JSON',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.xml': 'XML',
        '.txt': 'Text',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bat': 'Batch',
        '.ps1': 'PowerShell',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'Header',
        '.java': 'Java',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.ts': 'TypeScript',
        '.jsx': 'React',
        '.tsx': 'React',
    }
    file_type = categories.get(ext, 'Other')
    logging.info(f"Tipe file untuk {filename}: {file_type}")
    return file_type

def count_lines(file_path):
    """Menghitung jumlah baris dan baris kode (tanpa komentar) dalam sebuah file."""
    logging.info(f"Menghitung baris pada file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            logging.info(f"{file_path}: Total baris={len(lines)}, Baris kode={code_lines}")
            return len(lines), code_lines
    except FileNotFoundError:
        logging.error(f"File tidak ditemukan: {file_path}")
        return 0, 0
    except PermissionError:
        logging.error(f"Izin ditolak saat membaca: {file_path}")
        return 0, 0
    except Exception as e:
        logging.error(f"Error menghitung baris pada {file_path}: {str(e)}")
        return 0, 0

def calculate_code_complexity(file_path):
    """Menghitung kompleksitas kode menggunakan radon."""
    if radon is None:
        logging.warning("radon tidak tersedia, kompleksitas kode tidak dapat dihitung.")
        return None

    file_type = get_file_type(os.path.basename(file_path))
    if file_type != 'Python':
        logging.info(f"Melewati perhitungan kompleksitas kode untuk file non-Python: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Analisis kompleksitas siklomatik
        try:
            cc_result = radon.complexity.cc_rank(content)
        except TypeError as e:  # Tangkap TypeError secara spesifik
            logging.warning(f"Gagal menghitung kompleksitas siklomatik untuk {file_path}: {str(e)}")
            cc_result = None
        except Exception as e:
            logging.warning(f"Gagal menghitung kompleksitas siklomatik untuk {file_path}: {str(e)}")
            cc_result = None
        
        # Analisis baris kode mentah
        try:
            raw_result = radon.raw.analyze(content)
        except Exception as e:
            logging.warning(f"Gagal menghitung baris kode mentah untuk {file_path}: {str(e)}")
            raw_result = None
        
        if cc_result is None or raw_result is None:
            return None
        
        complexity_data = {
            'cyclomatic_complexity': cc_result,
            'loc': raw_result.loc,
            'lloc': raw_result.lloc,
            'sloc': raw_result.sloc,
            'comments': raw_result.comments,
            'multi': raw_result.multi,
            'blank': raw_result.blank
        }
        logging.info(f"Kompleksitas kode dihitung untuk {file_path}: {complexity_data}")
        return complexity_data
    except FileNotFoundError:
        logging.error(f"File tidak ditemukan: {file_path}")
        return None
    except PermissionError:
        logging.error(f"Izin ditolak saat membaca: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Gagal menghitung kompleksitas kode untuk {file_path}: {str(e)}")
        return None

# =============================================================================
# Section 2: Change Analysis Utilities
# =============================================================================

def get_change_type(file_path, prev_hash):
    """
    Menentukan tipe perubahan berdasarkan analisis konten file.
    Mengembalikan tipe perubahan seperti "new_file", "bugfix", "feature", dsb.
    """
    logging.info(f"Analisis perubahan untuk file: {file_path}")
    if prev_hash is None:
        logging.info("File baru ditemukan.")
        return "new_file"
    
    current_hash = get_file_hash(file_path)
    if current_hash == prev_hash:
        logging.info("Tidak ada perubahan pada file.")
        return "no_change"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        logging.error(f"File tidak ditemukan: {file_path}")
        return "error"
    except PermissionError:
        logging.error(f"Izin ditolak saat membaca: {file_path}")
        return "error"
    except Exception as e:
        logging.error(f"Gagal membaca file {file_path}: {str(e)}")
        return "binary_change"
    
    if re.search(r'fix|bug|issue|error|crash|problem', content, re.I):
        change = "bugfix"
    elif re.search(r'feat|feature|add|new|implement', content, re.I):
        change = "feature"
    elif re.search(r'doc|documentation|comment|explain', content, re.I):
        change = "documentation"
    elif re.search(r'refactor|improve|optimiz|clean|enhance', content, re.I):
        change = "refactor"
    elif re.search(r'test|spec|assert|mock', content, re.I):
        change = "test"
    elif re.search(r'style|format|lint|indent', content, re.I):
        change = "style"
    else:
        change = "update"
    
    logging.info(f"Jenis perubahan untuk {file_path}: {change}")
    return change

def get_diff_stats(file_path, prev_content):
    """
    Menghitung statistik perbedaan (diff) antara konten saat ini dan konten sebelumnya.
    """
    logging.info(f"Menghitung diff stats untuk file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_content = f.read()
        
        if prev_content is None:
            lines_added = len(current_content.splitlines())
            logging.info(f"Diff stats untuk {file_path}: lines_added={lines_added}")
            return {"lines_added": lines_added, "lines_removed": 0, "lines_changed": 0}
        
        diff = difflib.unified_diff(
            prev_content.splitlines(),
            current_content.splitlines()
        )
        
        lines_added = 0
        lines_removed = 0
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                lines_added += 1
            elif line.startswith('-') and not line.startswith('---'):
                lines_removed += 1
        
        stats = {
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "lines_changed": lines_added + lines_removed
        }
        logging.info(f"Diff stats untuk {file_path}: {stats}")
        return stats
    except FileNotFoundError:
        logging.error(f"File tidak ditemukan: {file_path}")
        return {"lines_added": 0, "lines_removed": 0, "lines_changed": 0}
    except PermissionError:
        logging.error(f"Izin ditolak saat membaca: {file_path}")
        return {"lines_added": 0, "lines_removed": 0, "lines_changed": 0}
    except Exception as e:
        logging.error(f"Error menghitung diff stats untuk {file_path}: {str(e)}")
        return {"lines_added": 0, "lines_removed": 0, "lines_changed": 0}

# =============================================================================
# Section 3: Git Utilities
# =============================================================================

def get_git_info(file_path):
    """Mengambil informasi commit git untuk sebuah file."""
    logging.info(f"Mengambil informasi git untuk file: {file_path}")
    try:
        git_log = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=format:{"commit": "%H", "author": "%an", "date": "%ad", "message": "%s"}', file_path],
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )
        if git_log:
            git_info = json.loads(git_log)
            logging.info(f"Informasi git ditemukan untuk {file_path}: {git_info}")
            return git_info
    except subprocess.CalledProcessError as e:
        logging.error(f"Perintah git gagal untuk {file_path}: {e}")
        return None
    except FileNotFoundError:
        logging.error(f"Git tidak ditemukan atau file tidak ada: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Gagal mengambil informasi git untuk {file_path}: {str(e)}")
    return None

# =============================================================================
# Section 4: Chart Generation Utilities
# =============================================================================

def generate_activity_chart(activity_data, output_path):
    """Menghasilkan grafik aktivitas (bar chart) dan menyimpannya sebagai PNG."""
    logging.info("Menghasilkan grafik aktivitas.")
    dates = list(activity_data.keys())
    counts = list(activity_data.values())
    
    plt.figure(figsize=(12, 6))
    plt.bar(dates, counts, color='skyblue')
    plt.xlabel('Date')
    plt.ylabel('Number of Changes')
    plt.title('Project Activity Over Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"Grafik aktivitas disimpan di: {output_path}")

def generate_file_type_chart(type_data, output_path):
    """Menghasilkan grafik distribusi tipe file (pie chart) dan menyimpannya sebagai PNG."""
    logging.info("Menghasilkan grafik distribusi tipe file.")
    labels = list(type_data.keys())
    sizes = list(type_data.values())
    
    plt.figure(figsize=(10, 10))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title('File Type Distribution')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logging.info(f"Grafik distribusi tipe file disimpan di: {output_path}")

# =============================================================================
# Section 5: Project Utilities
# =============================================================================

def load_gitignore(project_dir):
    """Memuat pola .gitignore jika file tersebut ada di direktori proyek."""
    logging.info("Memuat file .gitignore.")
    gitignore_path = os.path.join(project_dir, '.gitignore')
    
    if os.path.exists(gitignore_path):
        try:
            matches = gitignore_parser.parse_gitignore(gitignore_path)
            logging.info(f"Pola dimuat dari {gitignore_path}")
            return matches
        except Exception as e:
            logging.error(f"Gagal membaca .gitignore: {str(e)}")
            print("Warning: Could not read .gitignore file")
            return None
    else:
        logging.info(".gitignore tidak ditemukan.")
        return None

def is_ignored(file_path, project_dir, gitignore_matches):
    """Memeriksa apakah sebuah file harus diabaikan berdasarkan pola .gitignore."""
    if gitignore_matches is None:
        return False
    
    rel_path = os.path.relpath(file_path, project_dir)
    return gitignore_matches(file_path) # Gunakan gitignore_matches sebagai fungsi

# =============================================================================
# Section 6: Report Generation
# =============================================================================

def generate_progress_md(project_dir='.'):
    """
    Menghasilkan file .PROGRESS.md dan .PROGRESS.json berdasarkan aktivitas proyek.
    File grafik juga akan disimpan dalam folder .progress_charts.
    """
    logging.info("Memulai pembuatan laporan progress proyek.")
    # Buat direktori untuk grafik
    charts_dir = os.path.join(project_dir, '.progress_charts')
    os.makedirs(charts_dir, exist_ok=True)
    logging.info(f"Direktori grafik: {charts_dir}")
    
    # Muat pola .gitignore
    gitignore_matches = load_gitignore(project_dir)
    
    # Tambahkan file yang dihasilkan agar diabaikan
    generated_files = [
        '.PROGRESS.md',
        '.PROGRESS.json',
        '.progress_data.json',
        '.progress_charts/*',
        os.path.basename(__file__)
    ]
    # Tidak perlu lagi menambahkan ke gitignore_matches karena gitignore_parser menangani ini
    
    files = []
    file_hashes = {}
    file_contents = {}
    new_files = []
    
    # Muat data sebelumnya jika tersedia
    prev_data_path = os.path.join(project_dir, '.progress_data.json')
    try:
        with open(prev_data_path, 'r') as f:
            prev_data = json.load(f)
            prev_hashes = prev_data.get('hashes', {})
            prev_contents = prev_data.get('contents', {})
        logging.info("Data progress sebelumnya berhasil dimuat.")
    except FileNotFoundError:
        logging.warning("Tidak dapat menemukan data progress sebelumnya.")
        prev_hashes = {}
        prev_contents = {}
    except json.JSONDecodeError:
        logging.warning("Gagal memparse data progress sebelumnya (format JSON tidak valid).")
        prev_hashes = {}
        prev_contents = {}
    except Exception as e:
        logging.warning(f"Tidak dapat memuat data progress sebelumnya: {str(e)}")
        prev_hashes = {}
        prev_contents = {}
    
    # Konfigurasi proyek (tanpa config.json)
    project_name = "Telepon Bot"  # Ganti dengan nama proyek Anda
    project_description = "Sebuah bot Telegram untuk mengelola tugas, memberikan analisis, dan merespons pesan secara otomatis."  # Ganti dengan deskripsi proyek Anda
    project_keywords = ["telegram", "bot", "task management", "automation"]  # Ganti dengan kata kunci proyek Anda
    dependencies = ["python-telegram-bot", "SQLAlchemy"] # Ganti dengan dependensi proyek Anda
    
    # Telusuri file dalam direktori proyek
    for root, _, filenames in os.walk(project_dir):
        if any(part.startswith('.') for part in Path(root).parts):
            continue
        for filename in filenames:
            if (filename.startswith('.') or 
                filename == '.PROGRESS.md' or
                filename == '.PROGRESS.json' or
                filename == os.path.basename(__file__) or
                '.progress_charts' in root):
                continue
                
            file_path = os.path.join(root, filename)
            if is_ignored(file_path, project_dir, gitignore_matches):
                continue
            rel_path = os.path.relpath(file_path, project_dir)
            logging.info(f"Memproses file: {rel_path}")
            
            try:
                mod_time = os.path.getmtime(file_path)
                create_time = os.path.getctime(file_path)
                
                current_hash = get_file_hash(file_path)
                file_hashes[rel_path] = current_hash
                
                if rel_path not in prev_hashes:
                    new_files.append(rel_path)
                    logging.info(f"File baru terdeteksi: {rel_path}")
                
                if os.path.getsize(file_path) < 1024 * 1024:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_contents[rel_path] = f.read()
                    except FileNotFoundError:
                        logging.error(f"File tidak ditemukan: {rel_path}")
                    except PermissionError:
                        logging.error(f"Izin ditolak saat membaca: {rel_path}")
                    except Exception as e:
                        logging.error(f"Gagal membaca konten {rel_path}: {str(e)}")
                
                change_type = get_change_type(file_path, prev_hashes.get(rel_path))
                git_info = get_git_info(file_path)
                diff_stats = get_diff_stats(file_path, prev_contents.get(rel_path))
                total_lines, code_lines = count_lines(file_path)
                file_type = get_file_type(filename)
                
                # Hitung kompleksitas kode
                #code_complexity = calculate_code_complexity(file_path) # Hapus baris ini
                code_complexity = None # Set ke None

                file_info = {
                    'path': rel_path,
                    'last_modified_timestamp': datetime.datetime.fromtimestamp(mod_time).isoformat(),
                    'create_timestamp': datetime.datetime.fromtimestamp(create_time).isoformat(),
                    'change_type': change_type,
                    'file_type': file_type,
                    'lines': {
                        'total': total_lines,
                        'code': code_lines
                    },
                    'diff': diff_stats,
                    'git': git_info,
                    'code_complexity': code_complexity if code_complexity else None
                }
                
                # Ganti nilai None dengan nilai default
                for key, value in file_info.items():
                    if value is None:
                        file_info[key] = "" if isinstance(value, str) else 0 if isinstance(value, (int, float)) else []
                
                files.append(file_info)
            except Exception as e:
                logging.error(f"Error processing {file_path}: {str(e)}")
    
    # Urutkan file berdasarkan waktu modifikasi (terbaru dahulu)
    files.sort(key=lambda x: x['last_modified_timestamp'], reverse=True)
    
    # Kelompokkan file berdasarkan tanggal
    files_by_date = defaultdict(list)
    for file_info in files:
        date_str = datetime.datetime.fromisoformat(file_info['last_modified_timestamp']).strftime('%Y-%m-%d')
        files_by_date[date_str].append(file_info)
    
    activity_data = {date: len(files) for date, files in files_by_date.items()}
    file_type_counter = Counter([file_info['file_type'] for file_info in files])
    
    # Hasilkan grafik
    activity_chart_path = os.path.join(charts_dir, 'activity_chart.png')
    generate_activity_chart(activity_data, activity_chart_path)
    
    filetype_chart_path = os.path.join(charts_dir, 'filetype_chart.png')
    generate_file_type_chart(file_type_counter, filetype_chart_path)
    
    # Buat data progress dalam format JSON
    progress_data = {
        'project_name': project_name,
        'project_description': project_description,
        'project_keywords': project_keywords,
        'dependencies': dependencies,
        'last_updated': datetime.datetime.now().isoformat(),
        'total_files': len(files),
        'new_files': len(new_files),
        'file_types': dict(file_type_counter),
        'daily_activity': activity_data,
        'changes_by_date': {}
    }
    
    for date_str, file_list in files_by_date.items():
        progress_data['changes_by_date'][date_str] = {
            'files': [
                {
                    'path': file_info['path'],
                    'last_modified_timestamp': file_info['last_modified_timestamp'],
                    'change_type': file_info['change_type'],
                    'file_type': file_info['file_type'],
                    'lines': file_info['lines'],
                    'diff': file_info['diff'],
                    'git': file_info['git'],
                    'code_complexity': file_info['code_complexity']
                }
                for file_info in file_list
            ],
            'summary': {
                'total_changes': len(file_list),
                'by_type': dict(Counter([f['change_type'] for f in file_list])),
                'by_file_type': dict(Counter([f['file_type'] for f in file_list])),
                'lines_added': sum(f['diff']['lines_added'] for f in file_list),
                'lines_removed': sum(f['diff']['lines_removed'] for f in file_list)
            }
        }
    
    progress_json_path = os.path.join(project_dir, '.PROGRESS.json')
    with open(progress_json_path, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, indent=2)
    logging.info(f"File progress JSON berhasil disimpan di: {progress_json_path}")
    
    # Buat laporan dalam format Markdown
    md_content = "# Project Progress Report\n\n"
    md_content += "## 📊 Project Summary\n\n"
    md_content += f"- **Project Name:** {project_name}\n"
    md_content += f"- **Description:** {project_description}\n"
    md_content += f"- **Keywords:** {', '.join(project_keywords)}\n"
    md_content += f"- **Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md_content += f"- **Total Files:** {len(files)}\n"
    md_content += f"- **New Files:** {len(new_files)}\n"
    md_content += f"- **File Types:** {', '.join([f'{k} ({v})' for k, v in file_type_counter.most_common()])}\n\n"
    
    md_content += "## 📈 Activity Charts\n\n"
    md_content += f"![Activity Chart](.progress_charts/activity_chart.png)\n\n"
    md_content += f"![File Type Distribution](.progress_charts/filetype_chart.png)\n\n"
    
    md_content += "## 📆 Changes by Date\n\n"
    for date_str in sorted(files_by_date.keys(), reverse=True):
        file_list = files_by_date[date_str]
        summary = progress_data['changes_by_date'][date_str]['summary']
        md_content += f"### {date_str}\n\n"
        md_content += "#### Summary\n"
        md_content += f"- **Total Changes:** {summary['total_changes']}\n"
        if summary['by_type']:
            md_content += "- **Changes by Type:** "
            md_content += ", ".join([f"{k.replace('_', ' ').title()} ({v})" for k, v in summary['by_type'].items() if k != 'no_change'])
            md_content += "\n"
        md_content += f"- **Lines Added:** {summary['lines_added']}, **Lines Removed:** {summary['lines_removed']}\n\n"
        md_content += "#### Files Changed\n\n"
        for file_info in file_list:
            if file_info['change_type'] == 'no_change':
                continue
            time_str = datetime.datetime.fromisoformat(file_info['last_modified_timestamp']).strftime('%H:%M:%S')
            change_emoji = {
                'new_file': '🆕',
                'feature': '✨',
                'bugfix': '🐛',
                'documentation': '📝',
                'refactor': '♻️',
                'test': '🧪',
                'style': '💅',
                'update': '🔄',
                'binary_change': '📦'
            }.get(file_info['change_type'], '🔄')
            
            md_content += f"- {change_emoji} **`{file_info['path']}`** ({file_info['file_type']}) at {time_str}\n"
            diff = file_info['diff']
            if diff['lines_added'] > 0 or diff['lines_removed'] > 0:
                md_content += f"  - Changes: +{diff['lines_added']} -{diff['lines_removed']} lines\n"
            git = file_info['git']
            if git:
                md_content += f"  - Commit: {git['commit'][:7]} - {git['message']}\n"
            
            #if file_info['code_complexity']: # Hapus baris ini
            #    md_content += f"  - Cyclomatic Complexity: {file_info['code_complexity']['cyclomatic_complexity']}\n" # Hapus baris ini
            md_content += "\n"
    
    md_file_path = os.path.join(project_dir, '.PROGRESS.md')
    with open(md_file_path, 'w', encoding='utf-8') as f:
        md_content = md_content.replace('None', 'null')
        f.write(md_content)
    logging.info(f"File progress Markdown berhasil disimpan di: {md_file_path}")
    
    save_data = {
        'hashes': file_hashes,
        'contents': file_contents
    }
    with open(prev_data_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f)
    logging.info("Data progress sebelumnya berhasil diperbarui.")
    
    logging.info("✅ .PROGRESS.md and .PROGRESS.json successfully generated")
    logging.info(f"📊 Charts saved to {os.path.abspath(charts_dir)}")

# =============================================================================
# Section 7: Main Function
# =============================================================================

def main():
    logging.info("Memulai eksekusi utama.")
    generate_progress_md()
    logging.info("Selesai menjalankan skrip.")

if __name__ == "__main__":
    main()