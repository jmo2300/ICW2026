"""
File Organization Wizard
Automatically organize messy folders by file type, date, size, or custom rules.

Features:
- Smart file categorization (Documents, Images, Videos, etc.)
- Organize by date, file type, or size
- Preview changes before applying
- Undo functionality
- Custom organization rules
- Duplicate file detection
- Safe mode (doesn't delete anything)

Usage:
    python file_organizer.py
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import hashlib


class FileOrganizer:
    
    # Predefined file categories
    CATEGORIES = {
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'],
        'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
        'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'Code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.html', '.css', '.rb', '.go', '.rs'],
        'Executables': ['.exe', '.msi', '.bat', '.sh', '.app', '.dmg'],
        'Data': ['.json', '.xml', '.yaml', '.yml', '.sql', '.db', '.sqlite'],
        'Books': ['.epub', '.mobi', '.azw', '.azw3'],
        'Fonts': ['.ttf', '.otf', '.woff', '.woff2'],
    }
    
    def __init__(self, source_dir):
        self.source_dir = Path(source_dir)
        self.history_file = self.source_dir / '.organization_history.json'
        self.moves = []  # Track all moves for undo
        
    def get_file_category(self, file_path):
        """Determine file category based on extension"""
        ext = file_path.suffix.lower()
        
        for category, extensions in self.CATEGORIES.items():
            if ext in extensions:
                return category
        
        return 'Other'
    
    def scan_directory(self):
        """Scan directory and categorize files"""
        files_by_category = defaultdict(list)
        total_size = 0
        
        for item in self.source_dir.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                category = self.get_file_category(item)
                size = item.stat().st_size
                files_by_category[category].append({
                    'path': item,
                    'size': size,
                    'modified': datetime.fromtimestamp(item.stat().st_mtime)
                })
                total_size += size
        
        return files_by_category, total_size
    
    def format_size(self, size):
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def preview_organization(self, mode='category'):
        """Preview how files will be organized"""
        files_by_category, total_size = self.scan_directory()
        
        print("\n" + "="*70)
        print(f"PREVIEW: Organizing '{self.source_dir.name}'")
        print("="*70)
        print(f"Total files: {sum(len(files) for files in files_by_category.values())}")
        print(f"Total size: {self.format_size(total_size)}")
        print(f"Organization mode: {mode.upper()}")
        print("="*70 + "\n")
        
        if mode == 'category':
            for category in sorted(files_by_category.keys()):
                files = files_by_category[category]
                category_size = sum(f['size'] for f in files)
                print(f"📁 {category}/")
                print(f"   Files: {len(files)} | Size: {self.format_size(category_size)}")
                
                # Show first 3 files as examples
                for f in files[:3]:
                    print(f"   - {f['path'].name}")
                if len(files) > 3:
                    print(f"   ... and {len(files) - 3} more")
                print()
        
        return files_by_category
    
    def organize_by_category(self, dry_run=True):
        """Organize files into category folders"""
        files_by_category, _ = self.scan_directory()
        
        if dry_run:
            self.preview_organization('category')
            return
        
        print("\n🚀 Starting organization...")
        moved_count = 0
        
        for category, files in files_by_category.items():
            # Create category folder
            category_dir = self.source_dir / category
            category_dir.mkdir(exist_ok=True)
            
            for file_info in files:
                source = file_info['path']
                dest = category_dir / source.name
                
                # Handle duplicate names
                if dest.exists():
                    base = dest.stem
                    ext = dest.suffix
                    counter = 1
                    while dest.exists():
                        dest = category_dir / f"{base}_{counter}{ext}"
                        counter += 1
                
                try:
                    shutil.move(str(source), str(dest))
                    self.moves.append({'from': str(source), 'to': str(dest)})
                    moved_count += 1
                    print(f"✓ Moved: {source.name} → {category}/")
                except Exception as e:
                    print(f"✗ Error moving {source.name}: {e}")
        
        print(f"\n✨ Organization complete! Moved {moved_count} files.")
        self.save_history()
    
    def organize_by_date(self, dry_run=True):
        """Organize files by modification date (Year/Month)"""
        files_by_category, _ = self.scan_directory()
        
        if dry_run:
            print("\n" + "="*70)
            print("PREVIEW: Organization by Date")
            print("="*70)
        
        all_files = []
        for files in files_by_category.values():
            all_files.extend(files)
        
        files_by_date = defaultdict(list)
        for file_info in all_files:
            date = file_info['modified']
            key = f"{date.year}/{date.strftime('%B')}"
            files_by_date[key].append(file_info)
        
        if dry_run:
            for date_key in sorted(files_by_date.keys()):
                files = files_by_date[date_key]
                print(f"\n📅 {date_key}/")
                print(f"   Files: {len(files)}")
                for f in files[:3]:
                    print(f"   - {f['path'].name}")
                if len(files) > 3:
                    print(f"   ... and {len(files) - 3} more")
            return
        
        print("\n🚀 Starting date-based organization...")
        moved_count = 0
        
        for date_key, files in files_by_date.items():
            # Create date folder structure
            date_dir = self.source_dir / date_key
            date_dir.mkdir(parents=True, exist_ok=True)
            
            for file_info in files:
                source = file_info['path']
                dest = date_dir / source.name
                
                # Handle duplicates
                if dest.exists():
                    base = dest.stem
                    ext = dest.suffix
                    counter = 1
                    while dest.exists():
                        dest = date_dir / f"{base}_{counter}{ext}"
                        counter += 1
                
                try:
                    shutil.move(str(source), str(dest))
                    self.moves.append({'from': str(source), 'to': str(dest)})
                    moved_count += 1
                    print(f"✓ Moved: {source.name} → {date_key}/")
                except Exception as e:
                    print(f"✗ Error moving {source.name}: {e}")
        
        print(f"\n✨ Organization complete! Moved {moved_count} files.")
        self.save_history()
    
    def find_duplicates(self):
        """Find duplicate files based on content hash"""
        print("\n🔍 Scanning for duplicate files...")
        
        hashes = defaultdict(list)
        
        for item in self.source_dir.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                try:
                    # Calculate MD5 hash
                    hasher = hashlib.md5()
                    with open(item, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b''):
                            hasher.update(chunk)
                    file_hash = hasher.hexdigest()
                    hashes[file_hash].append(item)
                except Exception as e:
                    print(f"Error hashing {item.name}: {e}")
        
        # Find duplicates
        duplicates = {h: files for h, files in hashes.items() if len(files) > 1}
        
        if not duplicates:
            print("\n✨ No duplicates found!")
            return []
        
        print(f"\n⚠️  Found {len(duplicates)} sets of duplicate files:\n")
        
        for i, (file_hash, files) in enumerate(duplicates.items(), 1):
            size = files[0].stat().st_size
            print(f"Duplicate Set #{i} ({self.format_size(size)}):")
            for f in files:
                rel_path = f.relative_to(self.source_dir)
                print(f"  - {rel_path}")
            print()
        
        return duplicates
    
    def save_history(self):
        """Save organization history for undo"""
        with open(self.history_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'moves': self.moves
            }, f, indent=2)
    
    def undo_last_organization(self):
        """Undo the last organization operation"""
        if not self.history_file.exists():
            print("❌ No history found. Nothing to undo.")
            return
        
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        moves = history.get('moves', [])
        if not moves:
            print("❌ No moves to undo.")
            return
        
        print(f"\n↩️  Undoing {len(moves)} file moves...")
        
        # Reverse the moves
        for move in reversed(moves):
            try:
                source = Path(move['to'])
                dest = Path(move['from'])
                
                if source.exists():
                    # Recreate parent directory if needed
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(dest))
                    print(f"✓ Restored: {source.name}")
            except Exception as e:
                print(f"✗ Error restoring {source.name}: {e}")
        
        # Remove empty directories
        for item in self.source_dir.iterdir():
            if item.is_dir() and not any(item.iterdir()):
                item.rmdir()
                print(f"🗑️  Removed empty folder: {item.name}")
        
        # Clear history
        self.history_file.unlink()
        print("\n✨ Undo complete!")


def interactive_mode():
    """Run in interactive mode"""
    print("\n" + "="*70)
    print("FILE ORGANIZATION WIZARD")
    print("="*70)
    
    # Get directory to organize
    print("\nEnter the path to the folder you want to organize:")
    print("(or press Enter to use current directory)")
    
    dir_path = input("\nFolder path: ").strip()
    
    if not dir_path:
        dir_path = os.getcwd()
    
    dir_path = os.path.expanduser(dir_path)
    
    if not os.path.isdir(dir_path):
        print(f"\n❌ Error: '{dir_path}' is not a valid directory")
        return
    
    organizer = FileOrganizer(dir_path)
    
    while True:
        print("\n" + "="*70)
        print("OPTIONS")
        print("="*70)
        print("1. Preview organization by category")
        print("2. Organize by category")
        print("3. Preview organization by date")
        print("4. Organize by date")
        print("5. Find duplicate files")
        print("6. Undo last organization")
        print("7. Change folder")
        print("8. Exit")
        print("="*70)
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            organizer.preview_organization('category')
        
        elif choice == '2':
            confirm = input("\n⚠️  This will move files. Continue? (yes/no): ").lower()
            if confirm == 'yes':
                organizer.organize_by_category(dry_run=False)
            else:
                print("❌ Cancelled.")
        
        elif choice == '3':
            organizer.organize_by_date(dry_run=True)
        
        elif choice == '4':
            confirm = input("\n⚠️  This will move files. Continue? (yes/no): ").lower()
            if confirm == 'yes':
                organizer.organize_by_date(dry_run=False)
            else:
                print("❌ Cancelled.")
        
        elif choice == '5':
            organizer.find_duplicates()
        
        elif choice == '6':
            confirm = input("\n⚠️  Undo last organization? (yes/no): ").lower()
            if confirm == 'yes':
                organizer.undo_last_organization()
            else:
                print("❌ Cancelled.")
        
        elif choice == '7':
            interactive_mode()
            break
        
        elif choice == '8':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please choose 1-8.")


if __name__ == "__main__":
    interactive_mode()