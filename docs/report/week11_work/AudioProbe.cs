using System;
using System.Text;
using System.Runtime.InteropServices;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorCom { }

[ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator
{
    int EnumAudioEndpoints(int dataFlow, int stateMask, out IMMDeviceCollection devices);
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice device);
    int GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMDevice device);
}

[ComImport, Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection
{
    int GetCount(out int count);
    int Item(int index, out IMMDevice device);
}

[ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice
{
    int Activate(ref Guid iid, int clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object iface);
    int OpenPropertyStore(int access, out IPropertyStore store);
    int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id);
    int GetState(out int state);
}

[ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyStore
{
    int GetCount(out int count);
    int GetAt(int index, out PROPERTYKEY key);
    int GetValue(ref PROPERTYKEY key, out PROPVARIANT value);
    int SetValue(ref PROPERTYKEY key, ref PROPVARIANT value);
    int Commit();
}

[StructLayout(LayoutKind.Sequential, Pack = 4)]
struct PROPERTYKEY { public Guid fmtid; public int pid; }

[StructLayout(LayoutKind.Explicit, Size = 24)]
struct PROPVARIANT
{
    [FieldOffset(0)] public ushort vt;
    [FieldOffset(8)] public IntPtr pointer;
    [FieldOffset(8)] public int intValue;
    [FieldOffset(8)] public float floatValue;
}

[ComImport, Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume
{
    int RegisterControlChangeNotify(IntPtr notify);
    int UnregisterControlChangeNotify(IntPtr notify);
    int GetChannelCount(out int count);
    int SetMasterVolumeLevel(float level, Guid ctx);
    int SetMasterVolumeLevelScalar(float level, Guid ctx);
    int GetMasterVolumeLevel(out float level);
    int GetMasterVolumeLevelScalar(out float level);
    int SetChannelVolumeLevel(int ch, float level, Guid ctx);
    int SetChannelVolumeLevelScalar(int ch, float level, Guid ctx);
    int GetChannelVolumeLevel(int ch, out float level);
    int GetChannelVolumeLevelScalar(int ch, out float level);
    int SetMute(bool mute, Guid ctx);
    int GetMute(out bool mute);
}

[ComImport, Guid("f8679f50-850a-41cf-9c72-430f290290c8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPolicyConfig
{
    int GetMixFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceName, out IntPtr format);
    int GetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceName, bool def, out IntPtr format);
    int ResetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceName);
    int SetDeviceFormat([MarshalAs(UnmanagedType.LPWStr)] string deviceName, IntPtr endPointFormat, IntPtr mixFormat);
    int GetProcessingPeriod([MarshalAs(UnmanagedType.LPWStr)] string deviceName, bool def, IntPtr period, IntPtr min);
    int SetProcessingPeriod([MarshalAs(UnmanagedType.LPWStr)] string deviceName, IntPtr period);
    int GetShareMode([MarshalAs(UnmanagedType.LPWStr)] string deviceName, IntPtr mode);
    int SetShareMode([MarshalAs(UnmanagedType.LPWStr)] string deviceName, IntPtr mode);
    int GetPropertyValue([MarshalAs(UnmanagedType.LPWStr)] string deviceName, ref PROPERTYKEY key, out PROPVARIANT value);
    int SetPropertyValue([MarshalAs(UnmanagedType.LPWStr)] string deviceName, ref PROPERTYKEY key, ref PROPVARIANT value);
    int SetDefaultEndpoint([MarshalAs(UnmanagedType.LPWStr)] string deviceName, int role);
    int SetEndpointVisibility([MarshalAs(UnmanagedType.LPWStr)] string deviceName, bool visible);
}

[ComImport, Guid("870af99c-171d-4f9e-af0d-e63df40c2bc9")]
class PolicyConfigClientCom { }

public class AudioProbe
{
    static string Name(IMMDevice dev)
    {
        IPropertyStore ps;
        dev.OpenPropertyStore(0, out ps);
        var key = new PROPERTYKEY();
        key.fmtid = new Guid("a45c254e-df1c-4efd-8020-67d146a850e0");
        key.pid = 14;
        PROPVARIANT pv;
        ps.GetValue(ref key, out pv);
        if (pv.vt == 31 && pv.pointer != IntPtr.Zero) return Marshal.PtrToStringUni(pv.pointer);
        return "(vt=" + pv.vt + ")";
    }

    static void Volume(IMMDevice dev, out float level, out bool mute)
    {
        level = -1; mute = false;
        Guid iid = typeof(IAudioEndpointVolume).GUID;
        object o;
        if (dev.Activate(ref iid, 1, IntPtr.Zero, out o) != 0) return;
        var vol = (IAudioEndpointVolume)o;
        vol.GetMasterVolumeLevelScalar(out level);
        vol.GetMute(out mute);
        Marshal.ReleaseComObject(o);
    }

    public static string ListRender()
    {
        var sb = new StringBuilder();
        var en = (IMMDeviceEnumerator)(new MMDeviceEnumeratorCom());
        IMMDeviceCollection col;
        int hr = en.EnumAudioEndpoints(0, 1, out col);
        if (hr != 0) return "EnumAudioEndpoints hr=" + hr;
        int n; col.GetCount(out n);
        for (int i = 0; i < n; i++)
        {
            IMMDevice dev; col.Item(i, out dev);
            string id; dev.GetId(out id);
            float level; bool mute; Volume(dev, out level, out mute);
            sb.AppendLine(i + " | " + Name(dev) + " | " + id + " | " + Math.Round(level * 100) + "% | mute=" + mute);
            Marshal.ReleaseComObject(dev);
        }
        Marshal.ReleaseComObject(col);
        return sb.ToString();
    }

    public static string Check()
    {
        var sb = new StringBuilder();
        var en = (IMMDeviceEnumerator)(new MMDeviceEnumeratorCom());
        for (int r = 0; r < 3; r++)
        {
            IMMDevice dev;
            int hr = en.GetDefaultAudioEndpoint(0, r, out dev);
            if (hr != 0) { sb.AppendLine("default role " + r + ": none"); continue; }
            string id; dev.GetId(out id);
            float level; bool mute; Volume(dev, out level, out mute);
            sb.AppendLine("default role " + r + " | " + Name(dev) + " | " + id + " | " + Math.Round(level * 100) + "% | mute=" + mute);
            Marshal.ReleaseComObject(dev);
        }
        return sb.ToString();
    }

    public static string SetDefault(string id, int levelPercent)
    {
        var sb = new StringBuilder();
        var pc = (IPolicyConfig)(new PolicyConfigClientCom());
        for (int r = 0; r < 3; r++)
        {
            int hr = pc.SetDefaultEndpoint(id, r);
            sb.AppendLine("SetDefaultEndpoint role " + r + " hr=0x" + hr.ToString("X8"));
        }
        var en = (IMMDeviceEnumerator)(new MMDeviceEnumeratorCom());
        IMMDevice dev;
        int hr2 = en.GetDevice(id, out dev);
        if (hr2 == 0)
        {
            Guid iid = typeof(IAudioEndpointVolume).GUID;
            object o;
            if (dev.Activate(ref iid, 1, IntPtr.Zero, out o) == 0)
            {
                var vol = (IAudioEndpointVolume)o;
                vol.SetMute(false, Guid.Empty);
                vol.SetMasterVolumeLevelScalar(levelPercent / 100.0f, Guid.Empty);
                float level; bool mute; vol.GetMasterVolumeLevelScalar(out level); vol.GetMute(out mute);
                sb.AppendLine("volume=" + Math.Round(level * 100) + "% mute=" + mute);
                Marshal.ReleaseComObject(o);
            }
            Marshal.ReleaseComObject(dev);
        }
        else sb.AppendLine("GetDevice hr=0x" + hr2.ToString("X8"));
        return sb.ToString();
    }
}
