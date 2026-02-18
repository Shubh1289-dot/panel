FRCONSOLE.login(guna2TextBox1.Text, guna2TextBox2.Text);

var response = FRCONSOLE.response;

if (response.TryGetProperty("status", out var statusElement) &&
    statusElement.GetString() == "success")
{
    string message = FRCONSOLE.GetLatestMessage(guna2TextBox1.Text);

    if (!string.IsNullOrEmpty(message))
    {
        var msgDialog = new Guna2MessageDialog();
        msgDialog.Caption = "Admin Message";
        msgDialog.Text = message;
        msgDialog.Icon = MessageDialogIcon.Warning;
        msgDialog.Buttons = MessageDialogButtons.OK;
        msgDialog.Show();
    }

    status.Text = "Status: Login Success!";
    await Task.Delay(300);

    MAIN main = new MAIN();
    main.Show();
    this.Hide();
}
else
{
    // ✅ SAFE error message read
    if (response.TryGetProperty("message", out var msgElement))
        status.Text = "Status: " + msgElement.GetString();
    else
        status.Text = "Status: Login failed";
}