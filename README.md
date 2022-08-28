# CS50 Final Project - IP Mapper

## Description

If your reading this, your computer has network connections to other systems that could be anywhere, globally. The purpose of this project is to provide a visual display of the source of those IP connections on a dynamic map.

This project is a Windows GUI application developed with Python, leveraging Tkinter for the GUI Interface, and a SQLite3 database.    

Main features include:  

- Display a computers public NAT IP address
- Display the source location of a manually public IP Address
- Collect all active IP connections on your computer then display with markers on a map
- Generate a tabulated HTML table with all IP connections with their location

A demonstration of the video can be found at: https://youtu.be/W19ky5GfJUs 

<p align="left" width="100%">
  <img width="33%" src="images/ip-mapper.png">
  <img width="60%" src="images/map.png">
</p>



# Python Libraries Used

Libraries from other contributors used, include:

- IPinfo - translates IP Addresses to geolocation data
- ipaddress - simplifies working with IP Addresses
- folium - plots gps coordinates on a map
- tkinter - provides the GUI interface
- sqlite3 - database
- psutil - network connection utilities
- os - operating system utilities
- urllib - open http url
- time - used for sleep


# Project Setup on Windows

## Environment Setup

Install [Python for Windows](https://gitforwindows.org)

Clone the project from GitHub and run the following in PowerShell:

```
cd cs50-final-project
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## API Key

Register to obtain a free API key at [ipinfo.io](https://ipinfo.io/) for translating IP Addresses to geolocation data.  

## Environment Variable

Create a new User Variable

1. Run: `sysdm.cpl`
2. Click Advanced tab
3. Click Environment Variables
4. Click New under User Variables
5. Enter: 
   1. Variable name: API_KEY
   2. Variable value: {YOUR_API_KEY}


## Application Usage
Launch the application:  
`python main.py`  

# Application Details

Begin by creating a SQL database if it doesn't exist, then flushing the table. I found this to be more efficient than downloading to lists of lists, then sorting, filtering, converting to dictionaries, etc.

```python
# create database connection
conn = sqlite3.connect('geodb.db')
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS locations(
    id INTEGER PRIMARY KEY,
    address TEXT,
    geodata TEXT,
    city TEXT,
    state TEXT,
    region TEXT
    )''')
cur.execute("DELETE FROM locations")
conn.commit()
```

An environment variable with your registered API key is loaded into a variable, following best practices. I began testing the application by hardcoding the API key then ended up deleting the repository and starting over to remove it from history.

```python
# access token for ipinfo, register at ipinfo.io
API_KEY = os.getenv('API_KEY')
access_token = API_KEY
handler = ipinfo.getHandler(access_token)
```

This builds the initial frame for the Tkinter GUI application.

```python
# create tkinter frame
root = tk.Tk()
root.title("IP Mapper Widget")
# root.iconbitmap('globe.ico')
frm = ttk.Frame(root, relief="groove")
frm.grid(padx=5, pady=5, sticky="nw")
frm.columnconfigure(0, weight=1)
```

The following 2 functions demonstrate how to take a list of IP Addresses, extract geolocation information and save in a database table.

```python
def gps_coordinates(ip):
    """Translate IP address to longitude / latitude coordinates"""
    g = handler.getDetails(ip)
    return g


def convert_ip_to_gps_coordinates(addresses):
    """Refresh all geodata"""
    cur.execute("DELETE FROM locations")
    for ip in addresses:
        gps = gps_coordinates(str(ip))
        cur.execute('''
            INSERT INTO locations
            (address, geodata, city, state, region)
            VALUES (?,?,?,?,?)''', (str(ip), gps.loc, gps.city,
                                    gps.region, gps.country_name))
        conn.commit()
```

This function is uses the ipaddress library to validate an IP address when manually entered. The Help / About menu will list the CIDR ranges of private IP addresses that cannot route or be displayed on a map.

```python
def validate_ip(ip):
    '''Validate IP Address entry'''
    try:
        ipaddress.ip_address(ip)
        if (ipaddress.ip_address(ip)).is_private:
            msg = (ip + " is a private address, please enter a public IP!")
            popup("Not Valid", msg)
        else:
            generate_single_map(ip, "map_location.html")

    except:
        msg = (ip + " is NOT valid, try again!")
        popup("Not Valid", msg)
```

The function below takes a single IP address as an input, looks up the longitude/latitude coordinates, uses the folium library to plot on a map. The data is written to an html file and opened with the default browser.

```python
def generate_single_map(ip, filename):
    '''Add marker to map for single geoloction and display'''
    gps = gps_coordinates(ip)
    gps_location = (gps.loc).split(",")
    f = folium.Map(location=gps_location, zoom_start=10)
    dialog = gps.city + ", " + gps.region

    folium.Marker(
        location=gps_location,
        popup=dialog,
        icon=folium.Icon(color="green", icon="info-sign")
    ).add_to(f)

    f.save(save_dir + filename)
    try:
        os.startfile(save_dir + filename)
    except:
        print("Error: couldn't open file: ", filename)
```

