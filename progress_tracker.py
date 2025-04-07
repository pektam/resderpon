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

def get_file_hash(file_path):
    """Calculate the MD5 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def get_file_type(filename):
    """Determine file type based on extension"""
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
    return categories.get(ext, 'Other')

def get_change_type(file_path, prev_hash):
    """Determine type of change based on content analysis"""
    if prev_hash is None:
        return "new_file"
    
    current_hash = get_file_hash(file_path)
    if current_hash == prev_hash:
        return "no_change"
    
    # Basic change type detection based on file extension
    ext = os.path.splitext(file_path)[1].lower()
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        return "binary_change"
    
    # Look for indicators in code
    if re.search(r'fix|bug|issue|error|crash|problem', content, re.I):
        return "bugfix"
    elif re.search(r'feat|feature|add|new|implement', content, re.I):
        return "feature"
    elif re.search(r'doc|documentation|comment|explain', content, re.I):
        return "documentation"
    elif re.search(r'refactor|improve|optimiz|clean|enhance', content, re.I):
        return "refactor"
    elif re.search(r'test|spec|assert|mock', content, re.I):
        return "test"
    elif re.search(r'style|format|lint|indent', content, re.I):
        return "style"
    else:
        return "update"

def count_lines(file_path):
    """Count lines of code in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            return len(lines), code_lines
    except:
        return 0, 0

def get_git_info(file_path):
    """Get git commit information for a file"""
    try:
        git_log = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=format:{"commit": "%H", "author": "%an", "date": "%ad", "message": "%s"}', file_path],
            stderr=subprocess.DEVNULL,
            universal_newlines=True
        )
        if git_log:
            return json.loads(git_log)
    except:
        pass
    return None

def get_diff_stats(file_path, prev_content):
    """Calculate diff statistics between current and previous content"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_content = f.read()
        
        if prev_content is None:
            lines_added = len(current_content.splitlines())
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
        
        return {
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "lines_changed": lines_added + lines_removed
        }
    except:
        return {"lines_added": 0, "lines_removed": 0, "lines_changed": 0}

def generate_activity_chart(activity_data, output_path):
    """Generate activity chart as PNG"""
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

def generate_file_type_chart(type_data, output_path):
    """Generate file type distribution chart as PNG"""
    labels = list(type_data.keys())
    sizes = list(type_data.values())
    
    plt.figure(figsize=(10, 10))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title('File Type Distribution')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def load_gitignore(project_dir):
    """Load .gitignore patterns if the file exists"""
    gitignore_path = os.path.join(project_dir, '.gitignore')
    patterns = []
    
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except:
            print("Warning: Could not read .gitignore file")
    
    return patterns

def is_ignored(file_path, project_dir, gitignore_patterns):
    """Check if a file should be ignored based on .gitignore patterns"""
    # Get relative path for matching
    rel_path = os.path.relpath(file_path, project_dir)
    
    # Check against gitignore patterns
    for pattern in gitignore_patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            if fnmatch.fnmatch(rel_path + '/', pattern + '*'):
                return True
        # Handle file patterns
        elif fnmatch.fnmatch(rel_path, pattern):
            return True
        # Handle wildcard patterns
        elif '*' in pattern and fnmatch.fnmatch(rel_path, pattern):
            return True
        # Handle root directory patterns
        elif pattern.startswith('/') and fnmatch.fnmatch('/' + rel_path, pattern):
            return True
    
    return False

def generate_progress_md(project_dir='.'):
    """
    Generate PROGRESS.md file based on file modification dates with enhanced features
    """
    # Create output directory for charts
    charts_dir = os.path.join(project_dir, '.progress_charts')
    os.makedirs(charts_dir, exist_ok=True)
    
    # Load gitignore patterns
    gitignore_patterns = load_gitignore(project_dir)
    
    # Add files generated by this script to ignore list
    generated_files = [
        'PROGRESS.md',
        'PROGRESS.json',
        '.progress_data.json',
        '.progress_charts/*',
        os.path.basename(__file__)  # The script itself
    ]
    gitignore_patterns.extend(generated_files)
    
    # Get all files in the project directory
    files = []
    file_hashes = {}
    file_contents = {}
    new_files = []
    
    # Load previous data if available
    prev_data_path = os.path.join(project_dir, '.progress_data.json')
    try:
        with open(prev_data_path, 'r') as f:
            prev_data = json.load(f)
            prev_hashes = prev_data.get('hashes', {})
            prev_contents = prev_data.get('contents', {})
    except:
        prev_hashes = {}
        prev_contents = {}
    
    for root, _, filenames in os.walk(project_dir):
        # Skip hidden directories and .git
        if any(part.startswith('.') for part in Path(root).parts):
            continue
            
        for filename in filenames:
            # Skip hidden files, PROGRESS.md, and generated charts
            if (filename.startswith('.') or 
                filename == 'PROGRESS.md' or
                filename == 'PROGRESS.json' or
                filename == os.path.basename(__file__) or  # Skip the script itself
                '.progress_charts' in root):
                continue
                
            file_path = os.path.join(root, filename)
            
            # Skip files that match gitignore patterns
            if is_ignored(file_path, project_dir, gitignore_patterns):
                continue
            rel_path = os.path.relpath(file_path, project_dir)
            
            try:
                # Get file stats
                mod_time = os.path.getmtime(file_path)
                create_time = os.path.getctime(file_path)
                
                # Get file hash
                current_hash = get_file_hash(file_path)
                file_hashes[rel_path] = current_hash
                
                # Check if file is new or modified
                if rel_path not in prev_hashes:
                    new_files.append(rel_path)
                
                # For text files, store content for diff calculation
                if os.path.getsize(file_path) < 1024 * 1024:  # Skip files larger than 1MB
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_contents[rel_path] = f.read()
                    except:
                        pass
                
                # Get change type
                change_type = get_change_type(file_path, prev_hashes.get(rel_path))
                
                # Get git information
                git_info = get_git_info(file_path)
                
                # Get diff stats
                diff_stats = get_diff_stats(file_path, prev_contents.get(rel_path))
                
                # Count lines
                total_lines, code_lines = count_lines(file_path)
                
                # Get file type
                file_type = get_file_type(filename)
                
                # Append to files list
                files.append({
                    'path': rel_path,
                    'mod_time': mod_time,
                    'create_time': create_time,
                    'change_type': change_type,
                    'file_type': file_type,
                    'total_lines': total_lines,
                    'code_lines': code_lines,
                    'diff_stats': diff_stats,
                    'git_info': git_info
                })
            except Exception as e:
                # Skip problematic files
                print(f"Error processing {file_path}: {str(e)}")
    
    # Sort files by modification time (newest first)
    files.sort(key=lambda x: x['mod_time'], reverse=True)
    
    # Group files by date
    files_by_date = defaultdict(list)
    for file_info in files:
        date_str = datetime.datetime.fromtimestamp(file_info['mod_time']).strftime('%Y-%m-%d')
        files_by_date[date_str].append(file_info)
    
    # Generate activity data
    activity_data = {date: len(files) for date, files in files_by_date.items()}
    
    # Generate file type distribution
    file_type_counter = Counter([file_info['file_type'] for file_info in files])
    
    # Generate charts
    activity_chart_path = os.path.join(charts_dir, 'activity_chart.png')
    generate_activity_chart(activity_data, activity_chart_path)
    
    filetype_chart_path = os.path.join(charts_dir, 'filetype_chart.png')
    generate_file_type_chart(file_type_counter, filetype_chart_path)
    
    # Generate JSON data
    progress_data = {
        'last_updated': datetime.datetime.now().isoformat(),
        'total_files': len(files),
        'new_files': len(new_files),
        'file_types': dict(file_type_counter),
        'daily_activity': activity_data,
        'changes_by_date': {}
    }
    
    # Fill changes by date
    for date_str, file_list in files_by_date.items():
        progress_data['changes_by_date'][date_str] = {
            'files': [
                {
                    'path': file_info['path'],
                    'time': datetime.datetime.fromtimestamp(file_info['mod_time']).strftime('%H:%M:%S'),
                    'change_type': file_info['change_type'],
                    'file_type': file_info['file_type'],
                    'lines': {
                        'total': file_info['total_lines'],
                        'code': file_info['code_lines']
                    },
                    'diff': file_info['diff_stats'],
                    'git': file_info['git_info']
                }
                for file_info in file_list
            ],
            'summary': {
                'total_changes': len(file_list),
                'by_type': Counter([f['change_type'] for f in file_list]),
                'by_file_type': Counter([f['file_type'] for f in file_list]),
                'lines_added': sum(f['diff_stats']['lines_added'] for f in file_list),
                'lines_removed': sum(f['diff_stats']['lines_removed'] for f in file_list)
            }
        }
    
    # Save progress data as JSON for AI consumption
    progress_json_path = os.path.join(project_dir, 'PROGRESS.json')
    with open(progress_json_path, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, indent=2)
    
    # Generate human-readable markdown
    md_content = "# Project Progress Report\n\n"
    
    # Add summary section
    md_content += "## 📊 Project Summary\n\n"
    md_content += f"- **Last Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    md_content += f"- **Total Files:** {len(files)}\n"
    md_content += f"- **New Files:** {len(new_files)}\n"
    md_content += f"- **File Types:** {', '.join([f'{k} ({v})' for k, v in file_type_counter.most_common()])}\n\n"
    
    # Add charts section
    md_content += "## 📈 Activity Charts\n\n"
    md_content += f"![Activity Chart](.progress_charts/activity_chart.png)\n\n"
    md_content += f"![File Type Distribution](.progress_charts/filetype_chart.png)\n\n"
    
    # Add detailed changes by date
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
                
            time_str = datetime.datetime.fromtimestamp(file_info['mod_time']).strftime('%H:%M:%S')
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
            
            # Add diff stats if available
            diff = file_info['diff_stats']
            if diff['lines_added'] > 0 or diff['lines_removed'] > 0:
                md_content += f"  - Changes: +{diff['lines_added']} -{diff['lines_removed']} lines\n"
            
            # Add git commit info if available
            git = file_info['git_info']
            if git:
                md_content += f"  - Commit: {git['commit'][:7]} - {git['message']}\n"
            
            md_content += "\n"
    
    # Write to PROGRESS.md with UTF-8 encoding
    with open(os.path.join(project_dir, 'PROGRESS.md'), 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    # Save file hashes and contents for future diff calculation
    save_data = {
        'hashes': file_hashes,
        'contents': file_contents
    }
    with open(prev_data_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f)
    
    print(f"✅ PROGRESS.md and PROGRESS.json successfully generated")
    print(f"📊 Charts saved to {os.path.abspath(charts_dir)}")

if __name__ == "__main__":
    generate_progress_md()
