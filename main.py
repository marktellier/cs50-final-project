'''
CS50 final project

Status: Complete
'''

from ast import Not, Pass
import sqlite3
import ipinfo
import ipaddress
import psutil
import folium
import os
import urllib.request
import tkinter as tk
from tkinter import StringVar, ttk
import time

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

# access token for ipinfo, register at ipinfo.io
API_KEY = os.getenv('API_KEY')
access_token = API_KEY
handler = ipinfo.getHandler(access_token)

# create tkinter frame
root = tk.Tk()
root.title("IP Mapper Widget")
# root.iconbitmap('globe.ico')
frm = ttk.Frame(root, relief="groove")
frm.grid(padx=5, pady=5, sticky="nw")
frm.columnconfigure(0, weight=1)


def what_is_my_ip():
    """Obtain my firewall's public IP Address"""
    nat_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
    return nat_ip


def public_ip_addresses():
    """Obtain list of all public routable IP addresses from active connections"""
    publicIP = []
    activeConnections = psutil.net_connections(kind='tcp')
    for a in activeConnections:
        if a[4]:
            ip = ipaddress.ip_address(a[4][0])
            if not ip.is_private:
                publicIP.append(ip)
    return publicIP


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


def generate_map():
    '''Add geolocations to a map with circle relative to number city instances'''
    cur.execute("SELECT geodata, city, COUNT(city) FROM locations GROUP by city")
    locations = cur.fetchall()
    for location in locations:
        # add geo coordinates to map
        rad = 2 * location[2]
        if rad == 2:
            col = "red"
            fil = "#FFEBEE"
        elif rad < 10:
            col = "blue"
            fil = "#2196F3"
        elif rad < 15:
            col = "orange"
            fil = "#FBC02D"
        elif rad < 20:
            col = "green"
            fil = "#00BCD4"
        elif rad < 25:
            col = "purple"
            fil = "#AB47BC"
        else:
            col = "magenta"
            fil = "#F06292"
            rad = 30

        # map marker hover text
        pop = (str(location[2]) + " " + location[1])

        # add marker to map
        folium.CircleMarker(
            location=location[0].split(","),
            color=col,
            fill=True,
            fill_color=fil,
            radius=rad,
            popup=pop
        ).add_to(foliumMap)


def launch_map():
    '''Generate and launch map with geolocations'''
    generate_map()
    cur.execute("SELECT geodata FROM locations")
    tuple_bounds = list(cur.fetchall())

    if not len(tuple_bounds):
        popup("No Data", "Collect data with 'Set GeoData' first!")
    else:
        bounds = []
        for t in tuple_bounds:
            bounds.append(t[0].split(","))

        foliumMap.fit_bounds(bounds)
        foliumMap.save(save_dir + html_global)
        try:
            os.startfile(save_dir + html_global)
        except:
            print("Couldn't open", html_global)


def launch_report():
    '''Generate HTML report with geodata'''
    cur.execute(
        "SELECT address,city,state,region FROM locations ORDER BY region, state, city")
    locations = cur.fetchall()

    # validate table isn't empty
    if not len(locations):
        popup("No Data", "Collect data with 'Set GeoData' first!")
    else:
        report = save_dir + html_report
        f = open(report, 'w')
        head = '''
        <!DOCTYPE html>
        <html>
            <title>IP Connection Report</title>
            <style type="text/css">

                h1, h2, th, td
                {
                    padding: 20px;
                    text-align: left;
                    font-family: Verdana, Arial;
                }

                /* Table Border definition */
                table {
                    margin: auto;
                    box-shadow: 10px 10px 5px #888;
                    border: thin ridge grey;
                    width: 90%;
                }

                /* Table Header definition */
                th {
                    background: #5C6BC0;
                    color: #fff;
                    max-width: 400px;
                    padding: 5px 10px;
                    text-align: center;
                }

                /* Table Cell definition */
                td { font-size: 11px; padding: 5px 20px; color: #000; }

                /* Table Row, data color definition */
                tr { background: #b8d1f3; }

                /* Table Odd and Even Row Color definition */
                tr:nth-child(even) {
                    background: #dae5f4; }
                tr:nth-child(odd) {
                    background: #fff; }

                /* Table Row hover */
                tr:hover {
                    background: yellow; }

            </style>
        <head>
        </head>
        <table>
            <caption><h2>IP Address Table</h2></caption>
        <thead>
            <tr>
                <th scope="col">IP Address</th>
                <th scope="col">City</th>
                <th scope="col">Region</th>
                <th scope="col">Country</th>
            </tr>
        </thead>
        '''

        f.write(head)
        f.write("<tbody>")
        for i in locations:
            f.write("    <tr>")
            f.write("        <td>" + i[0] + "</td>")
            f.write("        <td>" + i[1] + "</td>")
            f.write("        <td>" + i[2] + "</td>")
            f.write("        <td>" + i[3] + "</td>")
            f.write("    </tr>")

        f.write("</tbody>\n</table>\n</html>")
        f.close()

        try:
            os.startfile(report)
        except:
            print("Error: couldn't open file: ", report)


def popup(title, message):
    popup = tk.Toplevel(root, padx=10, pady=10)
    popup.title(title)
    private_addresses = message
    label1 = ttk.Label(popup, text=private_addresses,
                       justify="left", font=('Courier 12'))
    label1.pack()


def update_status(text):
    status.set(text)
    root.update_idletasks()
    time.sleep(2)


def set_geodata():
    '''Collect geodata for all active, routable IP addresses'''
    status.set("Collecting Active Connections ...")
    root.update_idletasks()
    time.sleep(2)
    public_ips = public_ip_addresses()
    status.set("Converting Geo Data ...")
    root.update_idletasks()
    time.sleep(2)
    convert_ip_to_gps_coordinates(public_ips)
    time.sleep(2)
    status.set("Ready")


# Main
save_dir = os.path.expanduser("~") + "\\Downloads\\"
my_ip_address = what_is_my_ip()
foliumMap = folium.Map()
html_global = "global.html"
html_report = "geodata_report.html"

# Tkinter widget
label_frame1 = ttk.LabelFrame(frm, text="My Public IP Address")
label_frame1.grid(column=0, row=0, padx=5, pady=5, sticky="ew")
address_label = tk.Label(label_frame1, text=my_ip_address, font=26, width=30, anchor="w",
                         foreground="#00FF00", background="black", relief="sunken", bg="black", padx=5, pady=5)
address_label.grid(row=0, column=0, padx=5, pady=5)
button_a1 = ttk.Button(label_frame1, text="Map It", command=(
    lambda: generate_single_map(my_ip_address, "my_location.html")))
button_a1.grid(column=0, row=1, padx=5, pady=5, sticky="w")


label_frame2 = ttk.LabelFrame(frm, text="Enter Public IP Address")
label_frame2.grid(column=0, row=1, padx=5, pady=5, sticky="ew")
address_entry = ttk.Entry(
    label_frame2, textvariable="enterip", font=("courier", 16), justify="left")
address_entry.grid(row=0, column=0, padx=5, pady=5)
button_b1 = ttk.Button(label_frame2, text="Map It", command=(
    lambda: validate_ip(address_entry.get())))
button_b1.grid(column=0, row=1, padx=5, pady=5, sticky="w")


label_frame3 = ttk.LabelFrame(frm, text="Public Network Connections")
label_frame3.grid(column=0, row=2, padx=5, pady=5, sticky="ew")
status = StringVar()
status.set('Not Ready')
status_label = tk.Label(label_frame3, textvariable=status, font=26, width=30, anchor="w",
                        foreground="#00FF00", background="black", relief="sunken", bg="black", padx=5, pady=5)
status_label.grid(row=0, column=0, padx=5, pady=5)
button_c1 = ttk.Button(label_frame3, text="Set GeoData",
                       command=(lambda: set_geodata()))
button_c1.grid(column=0, row=1, padx=5, pady=5, sticky="w")
button_c2 = ttk.Button(label_frame3, text="Map It",
                       command=(lambda: launch_map()))
button_c2.grid(column=0, row=1, padx=5, pady=5, columnspan=2)

label_frame4 = ttk.LabelFrame(frm, text="Statistics Report")
label_frame4.grid(column=0, row=3, padx=5, pady=5, sticky="ew")
button_e1 = ttk.Button(label_frame4, text="Print It",
                       command=(lambda: launch_report()))
button_e1.grid(column=0, row=0, padx=5, pady=5)

# define top menu bar
mb = tk.Menu(root)
fm = tk.Menu(mb, tearoff=0)
fm.add_command(label='Exit', command=root.quit)
mb.add_cascade(label='File', menu=fm)

# define help menu (hm)
hm = tk.Menu(mb, tearoff=0)
about_title = "Routable IP Addresses"
about_message = '''
        Private Addresses

        All devices connected to your home network have a unique
        private IP Address assigned, but share a single public IP Address.
        The public IP Address is provided by your Internet Service
        Provider (ISP) and assigned to your router or firewall.
        This is referred to as Network Address Translation (NAT).

        The address ranges below are considered private, not routable
        to the internet and cannot be placed on map.

        CIDR             Address Range                   Class
        10.0.0.0/8       10.0.0.0 - 10.255.255.255       Class A
        172.16.0.0/12    172.16.0.0 - 172.31.255.255     Class B
        192.168.0.0/16   192.168.0.0 - 192.168.255.255   Class C
'''
hm.add_command(label='About', command=(
    lambda: popup(about_title, about_message)))
mb.add_cascade(label='Help', menu=hm)

root.config(menu=mb)
root.mainloop()
cur.close()
