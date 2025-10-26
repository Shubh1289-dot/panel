using System;
using System.Net.Http;
using System.Collections.Generic;
using Newtonsoft.Json;
using System.Text;

public static class HydraAuth
{
    public static dynamic response;

    private static readonly string apiUrl = "https://hydraauth.onrender.com/client_login";
    private static readonly string messageUrl = "https://hydraauth.onrender.com/get_messages";
    private static readonly string category = "ADMIN"; // <- Change this if needed

    private static string GetHWID()
    {
        return Environment.MachineName; // Simple HWID logic
    }

    public static void login(string username, string password)
    {
        using (var client = new HttpClient())
        {
            var values = new Dictionary<string, string>
            {
                { "category", category },
                { "username", username },
                { "password", password },
                { "hwid", GetHWID() }
            };

            var content = new FormUrlEncodedContent(values);
            try
            {
                var responseMessage = client.PostAsync(apiUrl, content).Result;
                string resultString = responseMessage.Content.ReadAsStringAsync().Result;
                response = JsonConvert.DeserializeObject(resultString);
            }
            catch (Exception ex)
            {
                response = new { status = "error", message = "Connection error: " + ex.Message };
            }
        }
    }

    public static string GetLatestMessage(string username)
    {
        using (var client = new HttpClient())
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
                dynamic msgData = JsonConvert.DeserializeObject(resString);

                if (msgData.status == "success" && msgData.messages != null && msgData.messages.Count > 0)
                {
                    var last = msgData.messages[msgData.messages.Count - 1];
                    return $"?? {last.time}\n\n{last.text}";
                }
            }
            catch (Exception ex)
            {
                return "? Failed to load message: " + ex.Message;
            }
        }

        return null;
    }
}