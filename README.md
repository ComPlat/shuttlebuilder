Welcome to the ShuttleBuilder
-----------------------------

Full documentation [here](https://chemotion.net/docs/eln/devices/configurations/data_transfer)

This application works independently of Electronic Lab Notebook (ELN) Chemotion. However, it is designed to operate as a service for Chemotion. The user administration of the Chemotion can also be mirrored. New users can be created by the admin or Chemotion users can log in with their Chemotion password and abbreviation.

![Diagram: Networg description](https://github.com/ComPlat/shuttlebuilder/blob/master/Assets/static/img/shuttle_builder.drawio.png)

The physical separation of laboratory PCs from public networks for security reasons significantly impacts the file transfer process requirements. Consequently, data stored locally on lab devices must be forwarded to the ELN via an intermediary system. The Shuttle is one part of such an intermediary system. It can facilitate this by sending device data to an intermediary data storage. It allows you to monitor and organize the data transmission of devices integrated with your ELN Chemotion instance (for more information, click [here](https://chemotion.net/docs/eln/devices/configurations/data_transfer) ). [Shuttle](https://github.com/ComPlat/shuttle) instances can be quickly and easily adapted to specific requirements. These instances can then be installed on the target lab system in just a few steps.

### How to set up a Shuttle Builder

Please use Docker image [mstarman/shuttlebuilder](https://hub.docker.com/r/mstarman/shuttlebuilder). Needed Enviroment variables are:

```
MODE=prod
# The host URL via which the service can be accessed 
ALLOWED_HOST=http://0.0.0.0
# The Chomtion URL only needed if you like to mirrow the user management
ELN_URL=https://XXXXXXXX
# Initial Super user information
DJANGO_SUPERUSER_USERNAME=Tom Riple
DJANGO_SUPERUSER_EMAIL=taent.riple@kit.edu
DJANGO_SUPERUSER_PASSWORD=QWer!1234
# Database information
DJANGO_POSTGRES_NAME=bridge
DJANGO_POSTGRES_USER=postgres
DJANGO_POSTGRES_PASSWORD=QWer!1234        
DJANGO_POSTGRES_PORT=5432
DJANGO_POSTGRES_HOST=db
```

### How to install Shuttle

The following section introduces the installation of the Shuttle. Note that the installation is **only** intended for Windows x64 and i386 devices and Linux x64 devices.

1.  **Generate Shuttle instance:**

    In Shuttle list you will find a new button. With this button you can create a new Shuttle instance adapted to an external WebDAV or SFTP server.

2.  **Download Shuttle instance:**

    After you have created a new Instance you can download the executable in the Shuttle list.

3.  **Install Shuttle instance:**

    The installation is simple but require administration rights.

    1.  Make a directory "C:\\Program Files\\eln\_exporter"
    2.  Copy the (on this server generated) **shuttle.exe** into "C:\\Program Files\\file\_exporter"
    3.  Copy the shuttle\_task.vbs into the startup directory.

        Hint: Press **Windows Key + R** to open run and type **shell:startup**. This will open startup directory

4.  **(SPECIAL CASE) Install Shuttle with SFTP on Windows XP:**

    As above the installation requires administration rights. The "Download" button leads to a zip file and not only to an executable file. This zipped file contains the executable file and WinSCP.

    1.  Make a directory "C:\\Program Files\\eln\_exporter"
    2.  Unzip the downloaded file **shuttle\_sftp\_winxp.zip**
    3.  Copy the **shuttle.exe**, **WinSCP.exe** andt **WinSCP.com** into "C:\\Program Files\\file\_exporter"
    4.  Copy the shuttle\_task.vbs into the startup directory.

        Hint: Press **Windows Key + R** to open run and type **shell:startup**. This will open startup directory

5.  **Install Shuttle on LINUX:**

    As above the installation requires administration rights. This installation description works only for **systemd**

    1.  Make a directory "/opt/file\_exporter"
    2.  Copy the **shuttle** into "/opt/file\_exporter/"
    3.  Download shuttle.service. Edit the file and enter the correct username. Copy it into /etc/systemd/system/shuttle.service. Run **systemctl start shuttle** to start it and **systemctl enable shuttle** to automatically get it to start on boot.