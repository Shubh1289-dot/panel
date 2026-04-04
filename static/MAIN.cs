   FORM 1


   public partial class Form1 : Form
    {
        DateTime expiryTime = DateTime.MinValue;

        public Form1()
        {
            InitializeComponent();
        }

        private async void guna2Button1_Click(object sender, EventArgs e)
        {
        label1.Text = "Logging...";

        var response = await FRCONSOLE.LoginAsync(
            guna2TextBox1.Text,
            textBox1.Text);

        if (response.TryGetProperty("status", out var s) &&
            s.GetString() == "success")
        {
            // ✅ EXPIRY READ SAFE
            if (response.TryGetProperty("expiry", out var expiryElement))
            {
                string expiryRaw = expiryElement.GetString();

                if (DateTime.TryParse(expiryRaw, out expiryTime))
                {
                    timer1.Interval = 1000;  // 1 sec
                    timer1.Start();          // ✅ CORRECT PLACE
                }
                else
                {
                    label1.Text = "Expiry parse failed";
                }
            }
            else
            {
                label1.Text = "Expiry missing";
            }
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

            MAIN m = new MAIN(expiryTime);
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

        private void timer1_Tick(object sender, EventArgs e)
        {
            TimeSpan left = expiryTime - DateTime.Now;

            if (left.TotalSeconds <= 0)
            {
                label1.Text = "Expired";
                timer1.Stop();
                await Task.Delay(1000);
                Application.Exit();
            return;
            }

            string text = "";

            if (left.Days > 0) text += left.Days + " days ";
            if (left.Hours > 0) text += left.Hours + " hours ";
            if (left.Minutes > 0) text += left.Minutes + " minutes ";

            text += left.Seconds + " seconds";

            label1.Text =
                "Expiry: " + expiryTime.ToString("dd MMM yyyy  HH:mm:ss") +
                "\nTime Left: " + text;
        }
    }
}

...................................................
MAIN.CS


    public partial class MAIN : Form
    {
        DateTime expiryTime;

        // ✅ Constructor jo expiry receive karega
        public MAIN(DateTime exp)
        {
            InitializeComponent();
            expiryTime = exp;

            timer1.Interval = 1000;   // 1 second
            timer1.Start();
        }

        private void MAIN_Load(object sender, EventArgs e)
        {
            label1.Text = "Expiry: " + expiryTime.ToString("dd MMM yyyy  HH:mm:ss");
        }

                private async void timer1_Tick(object sender, EventArgs e)
        {
            TimeSpan left = expiryTime - DateTime.Now;

            if (left.TotalSeconds <= 0)
            {
                label1.Text = "Expired";
                timer1.Stop();

                await Task.Delay(1000);
                Application.Exit();
                return;
            }

            string text = "";

            if (left.Days > 0) text += left.Days + " days ";
            if (left.Hours > 0) text += left.Hours + " hours ";
            if (left.Minutes > 0) text += left.Minutes + " minutes ";

            text += left.Seconds + " seconds";

            label1.Text =
                "Expiry: " + expiryTime.ToString("dd MMM yyyy  HH:mm:ss") +
                "\nTime Left: " + text;
        }
    }
}



//--------------------------------------------------for internal-------------------------------------------------------------------

main.cs





                // ✅ MAIN FORM WITH EXPIRY
                Main ML = new Main(mainHandle, expiryTime);<--------//this line
                ML.Show();
                this.Hide();



//---------------------------------------------------------------------------------------------------------------------------------------



               public Main(IntPtr handle, DateTime exp)

//---------------------------------------------------------------------------------------------------------------------------------------




    private async void Main_Load(object sender, EventArgs e)
    {
    label1.Text = "Expiry: " + expiryTime.ToString("dd MMM yyyy  HH:mm:ss");
     }


//---------------------------------------------------------------------------------------------------------------------------------------


private async void timer1_Tick(object sender, EventArgs e)
{
    TimeSpan left = expiryTime - DateTime.Now;

    if (left.TotalSeconds <= 0)
    {
        label1.Text = "Expired";
        timer1.Stop();
        await Task.Delay(1000);
        Application.Exit();
        return;
    }

    string text = "";

    if (left.Days > 0) text += left.Days + " days ";
    if (left.Hours > 0) text += left.Hours + " hours ";
    if (left.Minutes > 0) text += left.Minutes + " minutes ";

    text += left.Seconds + " seconds";

    label1.Text =
        "Expiry: " + expiryTime.ToString("dd MMM yyyy  HH:mm:ss") +
        "\nTime Left: " + text;
}

