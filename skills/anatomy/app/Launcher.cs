// Anatomy.exe: the app's launcher. The Start menu, desktop and login entries all point here.
//
//   Anatomy.exe                 start the local server if it is not running, then open the app window
//   Anatomy.exe --server        start the server only (used at Windows sign-in), no window
//   Anatomy.exe --root <dir>    projects folder (default C:\Anatomy)
//
// It is a Windows GUI program (no console): the server runs hidden, a small "Starting Anatomy"
// card shows while it comes up, and any failure is a plain message box, never a terminal.
// Built by install-anatomy.ps1 with the .NET Framework compiler that ships with Windows (C# 5).
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("Anatomy")]
[assembly: AssemblyProduct("Anatomy")]
[assembly: AssemblyDescription("Anatomy: dissect and rebuild a product")]
[assembly: AssemblyCompany("Lael Alexander")]
[assembly: AssemblyVersion("1.1.0.0")]

static class AnatomyLauncher
{
    const int Port = 4377;
    static readonly string Url = "http://127.0.0.1:" + Port + "/";
    static string AppDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
    static string Root = @"C:\Anatomy";
    static volatile bool done;

    [STAThread]
    static int Main(string[] args)
    {
        bool serverOnly = false;
        for (int i = 0; i < args.Length; i++)
        {
            string a = args[i].ToLowerInvariant();
            if (a == "--server" || a == "/server") serverOnly = true;
            else if ((a == "--root" || a == "/root") && i + 1 < args.Length) Root = args[++i];
        }
        Application.EnableVisualStyles();

        // One launcher at a time decides whether to start the server, so a click during sign-in
        // (when the login entry is already starting it) never starts a second copy.
        bool owned = false;
        using (Mutex gate = new Mutex(false, @"Local\AnatomyLauncher"))
        {
            try { owned = gate.WaitOne(TimeSpan.FromSeconds(120)); }
            catch (AbandonedMutexException) { owned = true; }
            try
            {
                if (!IsUp(2000))
                {
                    string err = StartServer(serverOnly);
                    if (err != null)
                    {
                        if (!serverOnly) MessageBox.Show(err, "Anatomy", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        return 1;
                    }
                }
            }
            finally { if (owned) gate.ReleaseMutex(); }
        }

        if (!serverOnly) { EnsureShortcuts(); OpenWindow(); }
        return 0;
    }

    // ---- server ------------------------------------------------------------------------

    static bool IsUp(int timeoutMs)
    {
        try
        {
            HttpWebRequest req = (HttpWebRequest)WebRequest.Create(Url + "api/health");
            req.Timeout = timeoutMs;
            req.ReadWriteTimeout = timeoutMs;
            req.Proxy = null;
            using (HttpWebResponse res = (HttpWebResponse)req.GetResponse())
            using (StreamReader r = new StreamReader(res.GetResponseStream()))
                return res.StatusCode == HttpStatusCode.OK && r.ReadToEnd().Contains("\"anatomy\"");
        }
        catch { return false; }
    }

    static string FindNode()
    {
        List<string> c = new List<string>();
        string path = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (string d in path.Split(';'))
            if (d.Trim().Length > 0) c.Add(Path.Combine(d.Trim().Trim('"'), "node.exe"));
        c.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), @"nodejs\node.exe"));
        c.Add(@"C:\Program Files\nodejs\node.exe");
        c.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), @"nodejs\node.exe"));
        c.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\nodejs\node.exe"));
        foreach (string p in c)
        {
            try { if (File.Exists(p)) return p; } catch { }
        }
        return null;
    }

    static void Rotate(string log)
    {
        try
        {
            FileInfo f = new FileInfo(log);
            if (f.Exists && f.Length > 5 * 1024 * 1024)
            {
                string old = log + ".old";
                if (File.Exists(old)) File.Delete(old);
                File.Move(log, old);
            }
        }
        catch { }
    }

    // Returns null when the server is up, or a plain-language reason it is not.
    static string StartServer(bool quiet)
    {
        string server = Path.Combine(AppDir, "server.js");
        if (!File.Exists(server))
            return "Anatomy's files are missing from " + AppDir + ".\n\nRun install-anatomy.ps1 again to repair it.";
        string node = FindNode();
        if (node == null)
            return "Anatomy needs Node.js, which was not found on this PC.\n\nRun install-anatomy.ps1 again, or install Node.js LTS from nodejs.org.";

        string log = Path.Combine(AppDir, "server.log");
        string errLog = Path.Combine(AppDir, "server.err.log");
        Rotate(log);
        Rotate(errLog);
        try { File.AppendAllText(errLog, "--- start " + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " ---\r\n"); } catch { }

        // cmd.exe only redirects the output to the log files; it and node both run with no window.
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = Path.Combine(Environment.SystemDirectory, "cmd.exe");
        psi.Arguments = "/d /s /c \"\"" + node + "\" \"" + server + "\" 1>>\"" + log + "\" 2>>\"" + errLog + "\"\"";
        psi.WorkingDirectory = AppDir;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.WindowStyle = ProcessWindowStyle.Hidden;
        // Clear markers inherited when started from inside a Claude Code session.
        List<string> drop = new List<string>();
        foreach (string k in psi.EnvironmentVariables.Keys)
        {
            string u = k.ToUpperInvariant();
            if (u == "CLAUDECODE" || u.StartsWith("CLAUDE_CODE_") || u == "ANTHROPIC_BASE_URL") drop.Add(k);
        }
        foreach (string k in drop) psi.EnvironmentVariables.Remove(k);
        psi.EnvironmentVariables["ANATOMY_ROOT"] = Root;
        psi.EnvironmentVariables["ANATOMY_PORT"] = Port.ToString();

        Process proc;
        try { proc = Process.Start(psi); }
        catch (Exception e) { return "Anatomy could not start its server: " + e.Message; }

        // Right after sign-in Node and antivirus scanning can be slow, so allow up to 90 s.
        Splash splash = quiet ? null : new Splash();
        done = false;
        bool ok = false;
        string exited = null;
        Thread poll = new Thread(delegate ()
        {
            Stopwatch sw = Stopwatch.StartNew();
            while (sw.Elapsed.TotalSeconds < 90)
            {
                if (IsUp(1500)) { ok = true; break; }
                if (proc.HasExited) { Thread.Sleep(1500); ok = IsUp(1500); if (!ok) exited = "stopped"; break; }
                Thread.Sleep(400);
            }
            done = true;
        });
        poll.IsBackground = true;
        poll.Start();
        if (splash != null) Application.Run(splash);
        poll.Join();
        if (ok) return null;

        string tail = Tail(errLog, 8);
        return (exited != null ? "Anatomy's server stopped while starting." : "Anatomy's server did not answer within 90 seconds.")
            + (tail.Length > 0 ? "\n\nLast lines of the error log:\n" + tail : "")
            + "\n\nLog: " + errLog;
    }

    static string Tail(string file, int n)
    {
        try
        {
            string[] lines = File.ReadAllLines(file);
            List<string> keep = new List<string>();
            for (int i = lines.Length - 1; i >= 0 && keep.Count < n; i--)
                if (lines[i].Trim().Length > 0 && !lines[i].StartsWith("--- start")) keep.Insert(0, lines[i]);
                else if (lines[i].StartsWith("--- start")) break;
            return string.Join("\n", keep.ToArray());
        }
        catch { return ""; }
    }

    // ---- shortcuts ---------------------------------------------------------------------

    // An install run from inside a packaged app (such as the Claude desktop app) has its new
    // AppData files, including Start menu entries, redirected into that app's private store,
    // where Windows cannot see them. The launcher runs as a normal program, so it (re)creates
    // the Start menu and sign-in entries itself when they are missing or point elsewhere.
    static void EnsureShortcuts()
    {
        string exe = Application.ExecutablePath;
        string ico = Path.Combine(AppDir, "anatomy.ico");
        if (!File.Exists(ico)) ico = exe;
        string rootArg = "--root \"" + Root + "\"";
        EnsureShortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Anatomy.lnk"),
            exe, rootArg, ico, "Anatomy: dissect and rebuild a product");
        EnsureShortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Startup), "Anatomy server.lnk"),
            exe, rootArg + " --server", ico, "Starts the Anatomy server in the background at sign-in");
    }

    static void EnsureShortcut(string lnkPath, string target, string arguments, string icon, string desc)
    {
        try
        {
            Type t = Type.GetTypeFromProgID("WScript.Shell");
            object shell = Activator.CreateInstance(t);
            object lnk = t.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { lnkPath });
            Type lt = lnk.GetType();
            string curTarget = (lt.InvokeMember("TargetPath", BindingFlags.GetProperty, null, lnk, null) as string) ?? "";
            string curArgs = (lt.InvokeMember("Arguments", BindingFlags.GetProperty, null, lnk, null) as string) ?? "";
            if (File.Exists(lnkPath) && string.Equals(curTarget, target, StringComparison.OrdinalIgnoreCase) && curArgs == arguments) return;
            lt.InvokeMember("TargetPath", BindingFlags.SetProperty, null, lnk, new object[] { target });
            lt.InvokeMember("Arguments", BindingFlags.SetProperty, null, lnk, new object[] { arguments });
            lt.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, lnk, new object[] { AppDir });
            lt.InvokeMember("IconLocation", BindingFlags.SetProperty, null, lnk, new object[] { icon + ",0" });
            lt.InvokeMember("Description", BindingFlags.SetProperty, null, lnk, new object[] { desc });
            lt.InvokeMember("Save", BindingFlags.InvokeMethod, null, lnk, null);
        }
        catch { }
    }

    // ---- window ------------------------------------------------------------------------

    static void OpenWindow()
    {
        string pf86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
        string pf = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        string edge = null;
        foreach (string p in new string[] { Path.Combine(pf86, @"Microsoft\Edge\Application\msedge.exe"), Path.Combine(pf, @"Microsoft\Edge\Application\msedge.exe") })
            if (File.Exists(p)) { edge = p; break; }
        try
        {
            if (edge != null)
            {
                // Its own profile folder makes Anatomy its own window and taskbar entry; keep that
                // profile bare (no sync, no extensions) so nothing else opens alongside it.
                string profile = Path.Combine(AppDir, "window");
                ProcessStartInfo psi = new ProcessStartInfo(edge,
                    "--app=" + Url + " --user-data-dir=\"" + profile + "\" --window-size=1400,900" +
                    " --no-first-run --no-default-browser-check --disable-sync --disable-extensions" +
                    " --disable-features=msImplicitSignin,msEdgeSyncConsent");
                psi.UseShellExecute = false;
                Process.Start(psi);
            }
            else Process.Start(Url);
        }
        catch (Exception e)
        {
            MessageBox.Show("Anatomy is running, but its window could not open: " + e.Message + "\n\nOpen " + Url + " in a browser.",
                "Anatomy", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    // Small borderless card shown while the server starts.
    class Splash : Form
    {
        public Splash()
        {
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.CenterScreen;
            ShowInTaskbar = true;
            Text = "Anatomy";
            Size = new Size(360, 120);
            BackColor = Color.FromArgb(24, 26, 31);
            TopMost = true;
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }
            PictureBox pic = new PictureBox();
            pic.SizeMode = PictureBoxSizeMode.Zoom;
            pic.Bounds = new Rectangle(24, 28, 64, 64);
            try { pic.Image = new Icon(Icon, 64, 64).ToBitmap(); } catch { }
            Label title = new Label();
            title.Text = "Anatomy";
            title.ForeColor = Color.White;
            title.Font = new Font("Segoe UI Semibold", 15f);
            title.Bounds = new Rectangle(104, 30, 240, 32);
            Label sub = new Label();
            sub.Text = "Starting\u2026";
            sub.ForeColor = Color.FromArgb(160, 168, 180);
            sub.Font = new Font("Segoe UI", 10f);
            sub.Bounds = new Rectangle(106, 64, 240, 24);
            Controls.Add(pic);
            Controls.Add(title);
            Controls.Add(sub);
            // Closes itself once the server check finishes (no cross-thread calls needed).
            System.Windows.Forms.Timer t = new System.Windows.Forms.Timer();
            t.Interval = 200;
            t.Tick += delegate { if (done) { t.Stop(); Close(); } };
            t.Start();
        }
    }
}
