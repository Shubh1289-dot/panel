using System;
using System.Net.Http;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using System.Security.Principal;
using System.Management;

public static class FRCONSOLE
{
    public static JsonElement response;

    private static readonly string apiUrl = "https://panel-9e9h.vercel.app/client_login";
    private static readonly string messageUrl = "https://panel-9e9h.vercel.app/get_messages";
    private static readonly string pingUrl = "https://panel-9e9h.vercel.app/ping";

    private static readonly string category = "HARSH";

    private static string currentUser = "";

    private static readonly HttpClient client = new HttpClient();

    // ?? FINAL HWID (SID + CPU + DISK)
    private static string GetHWID()
    {
        try
        {
            string sid = WindowsIdentity.GetCurrent().User.Value;
            string machine = Environment.MachineName;

            return $"{sid}|{machine}";
        }
        catch
        {
            return "UNKNOWN_HWID";
        }
    }

    // PC NAME (display only)
    private static string GetPCName()
    {
        return Environment.MachineName;
    }

    public static void login(string username, string password)
    {
        var values = new Dictionary<string, string>
        {
            { "category", category },
            { "username", username },
            { "password", password },
            { "hwid", GetHWID() },   // ?? STRONG HWID
            { "pcname", GetPCName() }
        };

        var content = new FormUrlEncodedContent(values);

        try
        {
            var responseMessage = client.PostAsync(apiUrl, content).Result;
            string resultString = responseMessage.Content.ReadAsStringAsync().Result;

            response = JsonSerializer.Deserialize<JsonElement>(resultString);

            if (response.GetProperty("status").GetString() == "success")
            {
                currentUser = username;
                _ = StartPing();
            }
        }
        catch (Exception ex)
        {
            string err = "{\"status\":\"error\",\"message\":\"Connection error: " + ex.Message + "\"}";
            response = JsonSerializer.Deserialize<JsonElement>(err);
        }
    }

    private static async Task StartPing()
    {
        while (true)
        {
            await Task.Delay(5000);

            try
            {
                var values = new Dictionary<string, string>
                {
                    { "category", category },
                    { "username", currentUser }
                };

                var content = new FormUrlEncodedContent(values);
                await client.PostAsync(pingUrl, content);
            }
            catch { }
        }
    }

    public static string GetLatestMessage(string username)
    {
        var values = new Dictionary<string, string>
        {
            { "category", category },
            { "username", username }
        };

        var content = new FormUrlEncodedContent(values);

        try
        {
            var res = client.PostAsync(messageUrl, content).Result;
            var resString = res.Content.ReadAsStringAsync().Result;
            var msgData = JsonSerializer.Deserialize<JsonElement>(resString);

            if (msgData.GetProperty("status").GetString() == "success" &&
                msgData.TryGetProperty("messages", out JsonElement list) &&
                list.GetArrayLength() > 0)
            {
                var last = list[list.GetArrayLength() - 1];
                return $"?? {last.GetProperty("time").GetString()}\n\n{last.GetProperty("text").GetString()}";
            }
        }
        catch (Exception ex)
        {
            return "? Failed: " + ex.Message;
        }

        return null;
    }
}