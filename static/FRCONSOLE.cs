using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using System.Security.Principal;

public static class FRCONSOLE
{
    private static readonly string apiUrl = "https://panel-9e9h.vercel.app/client_login";
    private static readonly string messageUrl = "https://panel-9e9h.vercel.app/get_messages";
    private static readonly string pingUrl = "https://panel-9e9h.vercel.app/ping";

    private static readonly string category = "HARSH";
    private static readonly HttpClient client = new HttpClient();

    private static readonly TimeSpan LoginTimeout = TimeSpan.FromSeconds(15);
    private static readonly TimeSpan MessageTimeout = TimeSpan.FromSeconds(5);
    private static readonly TimeSpan PingTimeout = TimeSpan.FromSeconds(5);

    private static string currentUser = "";
    private static CancellationTokenSource pingCancel;
    private static Task pingTask;
    private static readonly object lockObj = new object();

    // HWID
    private static string GetHWID()
    {
        try
        {
            string sid = WindowsIdentity.GetCurrent().User.Value;
            string machine = Environment.MachineName;
            return sid + "|" + machine;
        }
        catch
        {
            return "UNKNOWN_HWID";
        }
    }

    private static string GetPCName()
    {
        return Environment.MachineName;
    }

    // ?? LOGIN
    public static async Task<JsonElement> LoginAsync(string username, string password)
    {
        Dictionary<string, string> values = new Dictionary<string, string>()
        {
            { "category", category },
            { "username", username },
            { "password", password },
            { "hwid", GetHWID() },
            { "pcname", GetPCName() }
        };

        try
        {
            JsonElement res = await PostJson(apiUrl, values, LoginTimeout);

            if (IsSuccess(res))
                StartPing(username);

            return res;
        }
        catch
        {
            return Error("Connection error");
        }
    }

    // ?? MESSAGE
    public static async Task<string> GetLatestMessageAsync(string username)
    {
        Dictionary<string, string> values = new Dictionary<string, string>()
        {
            { "category", category },
            { "username", username }
        };

        try
        {
            JsonElement res = await PostJson(messageUrl, values, MessageTimeout);

            if (IsSuccess(res) &&
                res.TryGetProperty("messages", out JsonElement list) &&
                list.GetArrayLength() > 0)
            {
                JsonElement last = list[list.GetArrayLength() - 1];

                return "?? " + last.GetProperty("time").ToString() +
                       "\n\n" + last.GetProperty("text").ToString();
            }
        }
        catch { }

        return null;
    }

    // ?? PING LOOP
    private static void StartPing(string username)
    {
        lock (lockObj)
        {
            currentUser = username;

            if (pingCancel != null)
                pingCancel.Cancel();

            pingCancel = new CancellationTokenSource();

            pingTask = Task.Run(async () =>
            {
                while (!pingCancel.Token.IsCancellationRequested)
                {
                    try
                    {
                        await Task.Delay(5000, pingCancel.Token);

                        Dictionary<string, string> values = new Dictionary<string, string>()
                        {
                            { "category", category },
                            { "username", username }
                        };

                        await Post(pingUrl, values, PingTimeout, pingCancel.Token);
                    }
                    catch { }
                }
            });
        }
    }

    // ?? COMMON POST JSON
    private static async Task<JsonElement> PostJson(string url, Dictionary<string, string> data, TimeSpan timeout)
    {
        using (CancellationTokenSource cts = new CancellationTokenSource(timeout))
        using (FormUrlEncodedContent content = new FormUrlEncodedContent(data))
        {
            HttpResponseMessage res = await client.PostAsync(url, content, cts.Token);
            string str = await res.Content.ReadAsStringAsync();

            return JsonSerializer.Deserialize<JsonElement>(str);
        }
    }

    // ?? COMMON POST
    private static async Task Post(string url, Dictionary<string, string> data, TimeSpan timeout, CancellationToken token)
    {
        using (CancellationTokenSource cts = CancellationTokenSource.CreateLinkedTokenSource(token))
        {
            cts.CancelAfter(timeout);

            using (FormUrlEncodedContent content = new FormUrlEncodedContent(data))
            {
                await client.PostAsync(url, content, cts.Token);
            }
        }
    }

    private static bool IsSuccess(JsonElement json)
    {
        return json.TryGetProperty("status", out JsonElement s) &&
               s.GetString() == "success";
    }

    private static JsonElement Error(string msg)
    {
        string json = "{\"status\":\"error\",\"message\":\"" + msg + "\"}";
        return JsonSerializer.Deserialize<JsonElement>(json);
    }
}