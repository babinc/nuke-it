use clap::{CommandFactory, Parser};
use indicatif::{ProgressBar, ProgressStyle};
use rand::{Rng, RngCore};
use std::fs::{self, OpenOptions};
use std::io::{self, Seek, Write};
use std::path::{Path, PathBuf};

const RED: &str = "\x1b[1;31m";
const YELLOW: &str = "\x1b[1;33m";
const GREEN: &str = "\x1b[1;32m";
const DIM: &str = "\x1b[2m";
const RESET: &str = "\x1b[0m";
const BOLD: &str = "\x1b[1m";

mod art;

// ── One-liners ──────────────────────────────────────────────────────────

const SHRED_QUIPS: &[&str] = &[
    "It's time to kick ass and chew bubblegum... and I'm all outta gum.",
    "Your files are an inspiration for birth control.",
    "I ain't afraid of no quake!",
    "Let God sort 'em out!",
    "Blow it out your ass!",
    "Nobody steals our chicks... and lives!",
    "Get back to work, you slacker!",
    "Die, you son of a bitch!",
    "Piece of cake.",
    "Shake it, baby!",
];

const DONE_QUIPS: &[&str] = &[
    "Damn, I'm good.",
    "Hail to the king, baby!",
    "I'm gonna put this smack dab on your ass!",
    "Rest in pieces.",
    "Game over.",
    "That's gonna leave a mark!",
    "See you in hell!",
    "Your ass, your face — what's the difference?",
    "Clean up on aisle your whole damn drive.",
];

fn random_quip<'a>(quips: &'a [&'a str]) -> &'a str {
    let mut rng = rand::thread_rng();
    quips[rng.gen_range(0..quips.len())]
}

// ── CLI ─────────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(
    name = "nuke-it",
    version,
    about = "It's time to kick ass and chew bubblegum... and I'm all outta gum.",
    long_about = "It's time to kick ass and chew bubblegum... and I'm all outta gum.\n\n\
        nuke-it overwrites each file's contents with multiple passes of random data,\n\
        ones, and zeros before deleting it. Unlike moving to the recycle bin or a\n\
        simple delete, the original data cannot be recovered with file recovery tools.",
    after_help = "\x1b[1mExamples:\x1b[0m
  nuke-it secret.pdf                    Nuke a single file
  nuke-it -r ./old-projects/            Nuke a folder and everything in it
  nuke-it -n -r ./old-projects/         Preview what would be nuked (safe)
  nuke-it -y -p 7 *.pdf                 7 passes, skip confirmation
  nuke-it --wipe-free-space             Wipe free space on current drive
  nuke-it --wipe-free-space D:\\         Wipe free space on D:\\

  \x1b[2mNote: On SSDs, wear-leveling may retain old data at the firmware level.
  For SSDs, full-disk encryption (e.g. BitLocker) is the strongest guarantee.\x1b[0m"
)]
struct Args {
    /// Files or directories to nuke
    paths: Vec<PathBuf>,

    /// Number of overwrite passes [1 = fast, 3 = standard, 7+ = paranoid]
    #[arg(short, long, default_value_t = 3, value_parser = clap::value_parser!(u32).range(1..))]
    passes: u32,

    /// Skip the confirmation prompt (use with caution)
    #[arg(short = 'y', long)]
    yes: bool,

    /// Nuke directories and their contents
    #[arg(short, long)]
    recursive: bool,

    /// Show what would be nuked without deleting anything
    #[arg(short = 'n', long)]
    dry_run: bool,

    /// Wipe free space with random data to destroy previously deleted files
    #[arg(long, num_args = 0..=1, default_missing_value = ".", value_name = "PATH")]
    wipe_free_space: Option<PathBuf>,
}

// ── Utilities ───────────────────────────────────────────────────────────

fn format_size(bytes: u64) -> String {
    const KB: u64 = 1024;
    const MB: u64 = 1024 * KB;
    const GB: u64 = 1024 * MB;
    match bytes {
        b if b >= GB => format!("{:.1} GB", b as f64 / GB as f64),
        b if b >= MB => format!("{:.1} MB", b as f64 / MB as f64),
        b if b >= KB => format!("{:.1} KB", b as f64 / KB as f64),
        b => format!("{} B", b),
    }
}

fn confirm(prompt: &str) -> bool {
    print!("{}", prompt);
    let _ = io::stdout().flush();
    let mut input = String::new();
    if io::stdin().read_line(&mut input).is_err() {
        return false;
    }
    input.trim().eq_ignore_ascii_case("y")
}

fn is_symlink(path: &Path) -> bool {
    fs::symlink_metadata(path)
        .map(|m| m.file_type().is_symlink())
        .unwrap_or(false)
}

/// Collect all files under a path (recursively if dir), returning (files, total_bytes).
fn collect_targets(path: &Path, recursive: bool) -> io::Result<(Vec<PathBuf>, u64)> {
    let meta = fs::symlink_metadata(path)?;

    if meta.file_type().is_symlink() {
        return Err(io::Error::new(
            io::ErrorKind::Other,
            format!("refusing to follow symlink: {}", path.display()),
        ));
    }

    let mut files = Vec::new();
    let mut total = 0u64;

    if meta.is_dir() {
        if !recursive {
            return Err(io::Error::new(
                io::ErrorKind::Other,
                format!("is a directory (use -r): {}", path.display()),
            ));
        }
        for entry in fs::read_dir(path)? {
            let entry_path = entry?.path();
            if is_symlink(&entry_path) {
                eprintln!("{YELLOW}Skipping symlink:{RESET} {}", entry_path.display());
                continue;
            }
            let (sub_files, sub_total) = collect_targets(&entry_path, recursive)?;
            files.extend(sub_files);
            total += sub_total;
        }
    } else if meta.is_file() {
        total += meta.len();
        files.push(path.to_path_buf());
    } else {
        return Err(io::Error::new(
            io::ErrorKind::NotFound,
            format!("not found: {}", path.display()),
        ));
    }

    Ok((files, total))
}

/// Make a file writable on Windows (no-op on Unix).
#[cfg(windows)]
fn ensure_writable(path: &Path) -> io::Result<()> {
    let mut perms = fs::metadata(path)?.permissions();
    if perms.readonly() {
        perms.set_readonly(false);
        fs::set_permissions(path, perms)?;
    }
    Ok(())
}

#[cfg(not(windows))]
fn ensure_writable(_path: &Path) -> io::Result<()> {
    Ok(())
}

// ── Shredding core ──────────────────────────────────────────────────────

#[derive(Clone, Copy)]
enum FillPattern {
    Random,
    Fixed(u8),
}

const PASS_SEQUENCE: [FillPattern; 3] = [
    FillPattern::Random,
    FillPattern::Fixed(0xFF),
    FillPattern::Fixed(0x00),
];

fn write_pass(file: &mut fs::File, len: u64, rng: &mut impl RngCore, buf: &mut [u8], pattern: FillPattern) -> io::Result<()> {
    file.seek(io::SeekFrom::Start(0))?;
    let mut remaining = len;
    while remaining > 0 {
        let chunk = (remaining as usize).min(buf.len());
        match pattern {
            FillPattern::Random => rng.fill_bytes(&mut buf[..chunk]),
            FillPattern::Fixed(byte) => buf[..chunk].fill(byte),
        }
        file.write_all(&buf[..chunk])?;
        remaining -= chunk as u64;
    }
    Ok(())
}

const BUF_SIZE: usize = 1024 * 1024; // 1 MB

/// Overwrite file contents in place without deleting. Returns the file size.
fn overwrite_contents(path: &Path, passes: u32, buf: &mut [u8]) -> io::Result<u64> {
    let len = fs::symlink_metadata(path)?.len();
    if len == 0 {
        return Ok(0);
    }

    ensure_writable(path)?;

    let mut file = OpenOptions::new().write(true).open(path)?;
    let mut rng = rand::thread_rng();

    for pass in 0..passes {
        let pattern = PASS_SEQUENCE[(pass % 3) as usize];
        write_pass(&mut file, len, &mut rng, buf, pattern)?;
    }

    // Final random pass
    write_pass(&mut file, len, &mut rng, buf, FillPattern::Random)?;
    file.sync_all()?;

    Ok(len)
}

/// Rename a file to a random name in the same directory to scrub the original
/// file name from the directory entry. Returns the new path.
fn scramble_name(path: &Path) -> io::Result<PathBuf> {
    let parent = path.parent().unwrap_or(Path::new("."));
    let orig_name = path
        .file_name()
        .map(|n| n.to_string_lossy().len())
        .unwrap_or(8);
    let name_len = orig_name.max(8);

    let mut rng = rand::thread_rng();
    const CHARS: &[u8] = b"abcdefghijklmnopqrstuvwxyz0123456789";

    for _ in 0..10 {
        let name: String = (0..name_len)
            .map(|_| CHARS[rng.gen_range(0..CHARS.len())] as char)
            .collect();
        let new_path = parent.join(&name);
        match fs::rename(path, &new_path) {
            Ok(()) => return Ok(new_path),
            Err(e) if e.kind() == io::ErrorKind::AlreadyExists => continue,
            Err(e) => return Err(e),
        }
    }

    eprintln!(
        "  {YELLOW}Warning:{RESET} couldn't scramble name for {} {DIM}(deleting with original name){RESET}",
        path.display()
    );
    Ok(path.to_path_buf())
}

fn overwrite_file(path: &Path, passes: u32, buf: &mut [u8]) -> io::Result<()> {
    overwrite_contents(path, passes, buf)?;
    let final_path = scramble_name(path)?;
    fs::remove_file(&final_path)?;
    Ok(())
}

fn shred_path_with_progress(
    path: &Path,
    passes: u32,
    recursive: bool,
    pb: &ProgressBar,
    buf: &mut [u8],
) -> io::Result<usize> {
    let mut shredded = 0usize;
    if path.is_dir() {
        for entry in fs::read_dir(path)? {
            let entry_path = entry?.path();
            if is_symlink(&entry_path) {
                pb.suspend(|| {
                    eprintln!("{YELLOW}Skipping symlink:{RESET} {}", entry_path.display());
                });
                continue;
            }
            shredded += shred_path_with_progress(&entry_path, passes, recursive, pb, buf)?;
        }
        // Directory removal is best-effort — Windows may lock special folders
        // (e.g. Screenshots). The files inside are already gone, so this is cosmetic.
        match scramble_name(path).and_then(|p| fs::remove_dir(&p)) {
            Ok(()) => {}
            Err(e) => {
                pb.suspend(|| {
                    eprintln!(
                        "  {YELLOW}Warning:{RESET} couldn't remove directory {}: {} {DIM}(files inside were shredded successfully){RESET}",
                        path.display(),
                        e
                    );
                });
            }
        }
    } else if path.is_file() {
        let file_name = path
            .file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_default();
        pb.set_message(file_name);
        let size = fs::symlink_metadata(path)?.len();
        overwrite_file(path, passes, buf)?;
        pb.inc(size * (passes as u64 + 1));
        shredded += 1;
    }
    Ok(shredded)
}

fn print_dry_run(path: &Path, recursive: bool, depth: usize) -> io::Result<()> {
    let indent = "  ".repeat(depth);
    if is_symlink(path) {
        println!("  {YELLOW}SKIP{RESET} {}{} {DIM}(symlink){RESET}", indent, path.display());
        return Ok(());
    }
    if path.is_dir() {
        if !recursive {
            println!("  {YELLOW}SKIP{RESET} {}{} {DIM}(directory, use -r){RESET}", indent, path.display());
            return Ok(());
        }
        println!("  {RED}NUKE{RESET} {}{}/", indent, path.display());
        for entry in fs::read_dir(path)? {
            print_dry_run(&entry?.path(), recursive, depth + 1)?;
        }
    } else if path.is_file() {
        let size = fs::metadata(path)?.len();
        println!(
            "  {RED}NUKE{RESET} {}{} {DIM}({}){RESET}",
            indent,
            path.display(),
            format_size(size)
        );
    } else {
        println!("  {YELLOW}NOT FOUND{RESET} {}{}", indent, path.display());
    }
    Ok(())
}

// ── Free-space wipe ─────────────────────────────────────────────────────

fn get_available_space(path: &Path) -> io::Result<u64> {
    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        let wide: Vec<u16> = path.as_os_str().encode_wide().chain(std::iter::once(0)).collect();
        let mut free_bytes: u64 = 0;
        let ret = unsafe {
            windows_sys::Win32::Storage::FileSystem::GetDiskFreeSpaceExW(
                wide.as_ptr(),
                &mut free_bytes as *mut u64,
                std::ptr::null_mut(),
                std::ptr::null_mut(),
            )
        };
        if ret == 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(free_bytes)
    }
    #[cfg(not(windows))]
    {
        use std::ffi::CString;
        let c_path = CString::new(path.to_string_lossy().as_bytes())
            .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
        unsafe {
            let mut stat: libc::statvfs = std::mem::zeroed();
            if libc::statvfs(c_path.as_ptr(), &mut stat) != 0 {
                return Err(io::Error::last_os_error());
            }
            Ok(stat.f_bavail as u64 * stat.f_frsize as u64)
        }
    }
}

fn is_disk_full(e: &io::Error) -> bool {
    matches!(e.kind(), io::ErrorKind::StorageFull)
        || matches!(e.raw_os_error(), Some(28 | 39 | 112))
        // 28 = ENOSPC (Unix), 39 = ERROR_HANDLE_DISK_FULL (Windows), 112 = ERROR_DISK_FULL (Windows)
}

fn wipe_free_space(target_dir: &Path, yes: bool) -> io::Result<()> {
    if !target_dir.is_dir() {
        return Err(io::Error::new(
            io::ErrorKind::NotFound,
            format!("not a directory: {}", target_dir.display()),
        ));
    }

    let free = get_available_space(target_dir)?;

    print!("{}", art::DUKE_ART);
    println!("  {YELLOW}Free space wipe{RESET}");
    println!("    Target:     {}", target_dir.canonicalize()?.display());
    println!("    Free space: {}", format_size(free));
    println!();
    println!("  This will create a temporary file that fills the drive,");
    println!("  overwriting all free space with random data, then delete it.");
    println!("  {DIM}Your existing files will not be touched.{RESET}");
    println!();

    if !yes {
        if !confirm(&format!("  {YELLOW}Let's rock! Wipe it? [y/N]{RESET} ")) {
            println!("  Aborted.");
            return Ok(());
        }
        println!();
    }

    let temp_path = target_dir.join(".nuke-it-wipe.tmp");
    let result = do_wipe(&temp_path, free);

    // Always try to clean up, even on error
    let _ = fs::remove_file(&temp_path);

    result
}

fn do_wipe(temp_path: &Path, estimated_free: u64) -> io::Result<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(temp_path)?;

    let mut rng = rand::thread_rng();
    let mut buf = vec![0u8; BUF_SIZE];
    let mut written = 0u64;

    let pb = ProgressBar::new(estimated_free);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("  {bar:40.yellow/dim} {percent}%  {bytes}/{total_bytes}  {elapsed_precise} elapsed")
            .unwrap()
            .progress_chars("##-"),
    );

    // Write 1MB chunks until disk is full
    loop {
        rng.fill_bytes(&mut buf);
        match file.write_all(&buf) {
            Ok(()) => {
                written += BUF_SIZE as u64;
                pb.set_position(written.min(estimated_free));
            }
            Err(ref e) if is_disk_full(e) => break,
            Err(e) => {
                pb.finish_and_clear();
                return Err(e);
            }
        }
    }

    // Fill remaining bytes with small writes
    let small_buf = &mut buf[..4096];
    loop {
        rng.fill_bytes(small_buf);
        match file.write_all(small_buf) {
            Ok(()) => {
                written += small_buf.len() as u64;
                pb.set_position(written.min(estimated_free));
            }
            Err(ref e) if is_disk_full(e) => break,
            Err(e) => {
                pb.finish_and_clear();
                return Err(e);
            }
        }
    }

    let _ = file.sync_all();
    drop(file);

    pb.finish_and_clear();

    print!("{}", art::NUKE_ART);
    println!(
        "  {GREEN}Nuked.{RESET} Wrote {} of random data to free space.",
        format_size(written)
    );

    // Cleanup is handled by the caller
    Ok(())
}

// ── Main ────────────────────────────────────────────────────────────────

fn main() {
    let args = Args::parse();

    // Handle --wipe-free-space
    if let Some(ref target) = args.wipe_free_space {
        if let Err(e) = wipe_free_space(target, args.yes) {
            eprintln!("{RED}Error:{RESET} {}", e);
            std::process::exit(1);
        }
        return;
    }

    if args.paths.is_empty() {
        print!("{}", art::DUKE_BANNER);
        Args::command().print_help().unwrap();
        std::process::exit(0);
    }

    // Collect all targets to get file count and total size
    let mut all_files = Vec::new();
    let mut total_bytes = 0u64;
    let mut dir_count = 0usize;
    let mut collect_errors = Vec::new();

    for path in &args.paths {
        match collect_targets(path, args.recursive) {
            Ok((files, bytes)) => {
                if path.is_dir() {
                    dir_count += 1;
                }
                all_files.extend(files);
                total_bytes += bytes;
            }
            Err(e) => collect_errors.push(format!("{}: {}", path.display(), e)),
        }
    }

    if !collect_errors.is_empty() {
        for err in &collect_errors {
            eprintln!("{RED}Error:{RESET} {}", err);
        }
        if all_files.is_empty() {
            std::process::exit(1);
        }
    }

    let total_passes = args.passes + 1; // +1 for final random pass

    // Dry run mode
    if args.dry_run {
        print!("{}", art::DUKE_ART);
        println!("{YELLOW}DRY RUN{RESET} — nothing will be nuked:\n");
        for path in &args.paths {
            let _ = print_dry_run(path, args.recursive, 0);
        }
        println!(
            "\n  {DIM}Total: {} file(s), {}{RESET}\n",
            all_files.len(),
            format_size(total_bytes)
        );
        return;
    }

    // Confirmation prompt
    if !args.yes {
        print!("{}", art::DUKE_ART);
        let quip = random_quip(SHRED_QUIPS);
        println!("  {BOLD}\"{quip}\"{RESET}");
        println!();
        println!("  {RED}About to permanently nuke:{RESET}");
        println!(
            "    {} file(s){}totaling {}{}{} with {} overwrite {}",
            all_files.len(),
            if dir_count > 0 {
                format!(" across {} dir(s), ", dir_count)
            } else {
                ", ".to_string()
            },
            RED,
            format_size(total_bytes),
            RESET,
            total_passes,
            if total_passes == 1 { "pass" } else { "passes" },
        );
        println!();
        for path in &args.paths {
            let _ = print_dry_run(path, args.recursive, 0);
        }
        println!();
        if !confirm(&format!("  {RED}This CANNOT be undone. Let's rock! [y/N]{RESET} ")) {
            println!("  Aborted.");
            return;
        }
        println!();
    } else {
        let quip = random_quip(SHRED_QUIPS);
        println!("\n  {BOLD}\"{quip}\"{RESET}\n");
    }

    // Shred with progress bar
    let total_to_write = total_bytes * total_passes as u64;
    let pb = ProgressBar::new(total_to_write);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("  {bar:40.red/dim} {percent}%  {bytes}/{total_bytes}  {msg}")
            .unwrap()
            .progress_chars("##-"),
    );

    let mut buf = vec![0u8; BUF_SIZE];
    let mut shredded = 0usize;
    let mut errors = 0usize;
    for path in &args.paths {
        match shred_path_with_progress(path, args.passes, args.recursive, &pb, &mut buf) {
            Ok(count) => shredded += count,
            Err(e) => {
                pb.suspend(|| {
                    eprintln!("{RED}Error:{RESET} {}: {}", path.display(), e);
                });
                errors += 1;
            }
        }
    }

    pb.finish_and_clear();

    if shredded > 0 {
        print!("{}", art::NUKE_ART);
        let quip = random_quip(DONE_QUIPS);
        println!("  {BOLD}\"{quip}\"{RESET}");
        println!();
        println!(
            "  {GREEN}Nuked.{RESET} Shredded {} file(s), {} overwritten and removed.",
            shredded,
            format_size(total_bytes)
        );
    }
    if errors > 0 {
        eprintln!("  {RED}{} error(s) occurred.{RESET}", errors);
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::{self, File};
    use std::io::Read;

    fn temp_file(name: &str, content: &[u8]) -> PathBuf {
        let dir = std::env::temp_dir().join("nuke-it-tests");
        fs::create_dir_all(&dir).unwrap();
        let path = dir.join(name);
        fs::write(&path, content).unwrap();
        path
    }

    fn test_buf() -> Vec<u8> {
        vec![0u8; BUF_SIZE]
    }

    #[test]
    fn overwrite_destroys_original_content() {
        let secret = b"SSN: 123-45-6789 | INCOME: $95,000 | BANK ACCT: 9876543210";
        let path = temp_file("tax_data.txt", secret);
        let mut buf = test_buf();

        overwrite_contents(&path, 3, &mut buf).unwrap();

        let mut after = Vec::new();
        File::open(&path).unwrap().read_to_end(&mut after).unwrap();

        assert_eq!(after.len(), secret.len());
        assert_ne!(&after[..], &secret[..], "File content was NOT overwritten!");

        let after_str = String::from_utf8_lossy(&after);
        assert!(!after_str.contains("SSN"), "Original text fragments survived");
        assert!(!after_str.contains("123-45-6789"), "Original SSN survived");

        fs::remove_file(&path).unwrap();
    }

    #[test]
    fn shred_removes_file_from_disk() {
        let path = temp_file("delete_me.txt", b"sensitive data here");
        let mut buf = test_buf();
        assert!(path.exists());
        overwrite_file(&path, 3, &mut buf).unwrap();
        assert!(!path.exists(), "File still exists after shredding!");
    }

    #[test]
    fn shred_empty_file() {
        let path = temp_file("empty.txt", b"");
        let mut buf = test_buf();
        assert!(path.exists());
        overwrite_file(&path, 3, &mut buf).unwrap();
        assert!(!path.exists(), "Empty file still exists after shredding!");
    }

    #[test]
    fn shred_large_file_across_chunks() {
        let size = 200 * 1024;
        let secret: Vec<u8> = (0..size).map(|i| b'A' + (i % 26) as u8).collect();
        let path = temp_file("large_file.bin", &secret);
        let mut buf = test_buf();

        overwrite_contents(&path, 3, &mut buf).unwrap();

        let after = fs::read(&path).unwrap();
        assert_eq!(after.len(), size);
        assert_ne!(after, secret, "Large file content was NOT overwritten!");

        let pattern = &secret[..1024];
        for chunk in after.chunks(1024) {
            assert_ne!(chunk, &pattern[..chunk.len()], "Original pattern found");
        }

        fs::remove_file(&path).unwrap();
    }

    #[test]
    fn shred_directory_recursively() {
        let dir = std::env::temp_dir().join("nuke-it-tests").join("tax_folder");
        let sub = dir.join("subfolder");
        fs::create_dir_all(&sub).unwrap();
        fs::write(dir.join("w2.pdf"), b"W2 form data").unwrap();
        fs::write(sub.join("1099.pdf"), b"1099 form data").unwrap();

        let pb = ProgressBar::hidden();
        let mut buf = test_buf();
        shred_path_with_progress(&dir, 3, true, &pb, &mut buf).unwrap();

        assert!(!dir.exists(), "Directory still exists after recursive shred!");
    }

    #[test]
    fn format_size_works() {
        assert_eq!(format_size(500), "500 B");
        assert_eq!(format_size(1024), "1.0 KB");
        assert_eq!(format_size(1536), "1.5 KB");
        assert_eq!(format_size(1048576), "1.0 MB");
        assert_eq!(format_size(1073741824), "1.0 GB");
    }

    #[test]
    fn collect_targets_counts_correctly() {
        let dir = std::env::temp_dir().join("nuke-it-tests").join("collect_test");
        let sub = dir.join("inner");
        fs::create_dir_all(&sub).unwrap();
        fs::write(dir.join("a.txt"), b"aaaa").unwrap();
        fs::write(sub.join("b.txt"), b"bbbbbb").unwrap();

        let (files, total) = collect_targets(&dir, true).unwrap();
        assert_eq!(files.len(), 2);
        assert_eq!(total, 10);

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn passes_must_be_at_least_one() {
        let path = temp_file("one_pass.txt", b"secret stuff");
        let mut buf = test_buf();
        let size = overwrite_contents(&path, 1, &mut buf).unwrap();
        assert_eq!(size, 12);
        assert!(path.exists());

        let after = fs::read(&path).unwrap();
        assert_ne!(&after[..], b"secret stuff");

        fs::remove_file(&path).unwrap();
    }

    #[test]
    fn overwrite_returns_u64_size() {
        let path = temp_file("size_check.txt", b"hello");
        let mut buf = test_buf();
        let size = overwrite_contents(&path, 1, &mut buf).unwrap();
        assert_eq!(size, 5u64);
        fs::remove_file(&path).unwrap();
    }

    #[test]
    fn scramble_name_removes_original_name() {
        let path = temp_file("tax_return_2025.pdf", b"W2 data");
        let parent = path.parent().unwrap().to_path_buf();

        let new_path = scramble_name(&path).unwrap();

        assert!(!path.exists(), "Original file name still exists");
        assert!(new_path.exists(), "Renamed file doesn't exist");
        let new_name = new_path.file_name().unwrap().to_string_lossy();
        assert!(
            !new_name.contains("tax"),
            "Original name fragment 'tax' found in scrambled name"
        );
        assert!(
            !new_name.contains("2025"),
            "Original name fragment '2025' found in scrambled name"
        );
        assert_eq!(new_path.parent().unwrap(), parent);

        fs::remove_file(&new_path).unwrap();
    }

    #[test]
    fn shred_file_leaves_no_original_name() {
        let dir = std::env::temp_dir().join("nuke-it-tests").join("name_check");
        fs::create_dir_all(&dir).unwrap();
        let path = dir.join("super_secret_taxes.pdf");
        fs::write(&path, b"confidential").unwrap();
        let mut buf = test_buf();

        overwrite_file(&path, 1, &mut buf).unwrap();

        assert!(!path.exists());
        let remaining: Vec<_> = fs::read_dir(&dir).unwrap().collect();
        assert!(
            remaining.is_empty(),
            "Files left in directory after shred: {:?}",
            remaining
        );

        let _ = fs::remove_dir_all(&dir);
    }
}
