private bool isLoggingIn;


 private async void button1_Click(object sender, EventArgs e)
 {
     label1.Text = "Logging...";

     var response = await FRCONSOLE.LoginAsync(
         guna2TextBox1.Text,
         textBox1.Text);

     if (response.TryGetProperty("status", out var s) &&
         s.GetString() == "success")
     {
         
         string msg = await FRCONSOLE.GetLatestMessageAsync(guna2TextBox1.Text);

         if (!string.IsNullOrEmpty(msg))
         {
             new Guna2MessageDialog()
             {
                 Caption = "Admin Message",
                 Text = msg,
                 Icon = MessageDialogIcon.Warning,
                 Buttons = MessageDialogButtons.OK
             }.Show();
         }

         MAIN m = new MAIN();
         m.Show();
         this.Hide();
     }
     else
     {
         label1.Text = response.TryGetProperty("message", out var m)
             ? m.GetString()
             : "Login failed";
     }
 }