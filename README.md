Welcome to the ShuttleBuilder
-----------------------------

Full documentation [here](https://chemotion.net/docs/eln/devices/configurations/data_transfer)

This application works independently of the Electronic Lab Notebook (ELN) Chemotion. However, it is designed to operate as a service for Chemotion. The user can log in with his/her Chemotion password and abbreviation. However, the superuser can also create Locel users.

![Diagram: Networg description](https://github.com/ComPlat/shuttlebuilder/blob/master/Assets/static/img/shuttle_builder.drawio.png)

The physical separation of laboratory PCs from public networks for security reasons significantly
impacts the file transfer process requirements. Consequently, data stored locally 
on lab devices must be forwarded to the ELN via an intermediary system. The Shuttle 
is one part of such an intermediary system. It can facilitate this by sending device data 
to an intermediary data storage. It allows you to monitor and organize the data transmission of 
devices integrated with your ELN Chemotion instance (for more information, click [here](https://chemotion.net/docs/eln/devices/configurations/data_transfer) ). [Shuttle](https://github.com/ComPlat/shuttle) 
instances can be quickly and easily adapted to specific requirements. These instances can then be installed on the target lab system in just a few steps.

## How to set up a Shuttle Builder

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
POSTGRES_DB=builder
POSTGRES_USER=postgres
POSTGRES_PASSWORD=QWer!1234        
POSTGRES_PORT=5432
POSTGRES_HOST=db
```

# Basic Documentation

Full documentation [here](https://chemotion.net/docs/eln/devices/configurations/data_transfer).

After reading this documentation, users will gain a very good understanding of the Shuttle system, its purpose, and how it integrates with the Electronic Lab Notebook (ELN) Chemotion.  

The Shuttle application works independently of Chemotion but is designed to operate as a service for it. Users can log in with their Chemotion password and abbreviation, while superusers can also create local users [here](/admin/).

![Diagram: Network description](/static/img/shuttle_builder.drawio.png)

Due to the physical separation of laboratory PCs from public networks for security reasons, transferring files from lab devices to the ELN requires an intermediary system. Shuttle is a key component of this process, enabling device data to be sent to an intermediary storage system.  

It allows users to monitor and manage data transmission from devices integrated with their ELN Chemotion instance. Shuttle instances are flexible and can be adapted to specific requirements, then installed on target lab systems in just a few steps. For more information, see the [full documentation](https://chemotion.net/docs/eln/devices/configurations/data_transfer) or visit the [Shuttle GitHub repository](https://github.com/ComPlat/shuttle).

---

## How to install Shuttle

This section explains how to install Shuttle. Following these instructions will give users a strong understanding of the installation process. Installation is supported for Windows x64 and i386 devices, and Linux x64 devices.

1. **Generate Shuttle instance:**  
   In the Shuttle list, click the new instance button to create a [Shuttle instance](/shuttle-instance-list/shuttle-instance-edit) configured for an external WebDAV or SFTP server.

2. **Download Shuttle instance:**  
   After creating a new instance, download the executable from the Shuttle list.

3. **Install Shuttle instance:**  
   Installation is straightforward but requires administrative rights.  
   Steps:
   1. Make a directory: `C:\Program Files\eln_exporter`
   2. Copy the generated `shuttle.exe` into `C:\Program Files\file_exporter`
   3. Copy the [shuttle_task.vbs](/sdc_view/main_app/download/file_exporter_task.vbs) into the startup directory.  
      **Hint:** Press **Windows Key + R**, type `shell:startup`, and press Enter.

4. **(Special case) Install Shuttle with SFTP on Windows XP:**  
   This installation also requires administrative rights. The downloaded zip file contains both the executable and WinSCP.  
   Steps:
   1. Make a directory: `C:\Program Files\eln_exporter`
   2. Unzip `shuttle_sftp_winxp.zip`
   3. Copy `shuttle.exe`, `WinSCP.exe`, and `WinSCP.com` into `C:\Program Files\file_exporter`
   4. Copy the [shuttle_task.vbs](/sdc_view/main_app/download/file_exporter_task.vbs) into the startup directory.  
      **Hint:** Press **Windows Key + R**, type `shell:startup`, and press Enter.

5. **Install Shuttle on Linux:**  
   Installation requires administrative rights and is designed for **systemd**.  
   Steps:
   1. Make a directory: `/opt/file_exporter`
   2. Copy the `shuttle` executable into `/opt/file_exporter/`
   3. Download [shuttle.service](/sdc_view/main_app/download/shuttle.service), update it with the correct username, copy it into `/etc/systemd/system/shuttle.service`, then run:  
      ```bash
      systemctl start shuttle
      systemctl enable shuttle
      ```

---

## Preprocess Scripts

Shuttle supports preprocess scripts, allowing custom file manipulations before transfer. Understanding how to use these scripts gives users deeper insight into Shuttle’s flexibility.

- **Windows:** Scripts must be `.exe` files  
- **Linux:** All executable file types are supported

### Preprocess Script Requirements

Scripts must be placed in:

Linux: 
```bash
~/shuttle/scripts
```

Windows:
```bash
%USERPROFILE%\shuttle\scripts
```

If Shuttle has already run, this folder will exist.

Scripts are called for each file to be sent. They receive one argument: the absolute path to the file. The script can overwrite the file or create a new copy in the same folder, giving users full control over file preprocessing.