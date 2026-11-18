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
   Installation is straightforward but requires administrative rights. Every zip file contains an `INSTALL.txt` with the steps for this instance (without any secrets).  
   Windows (64 Bit and i386):
   1. Make a directory: `C:\Program Files\Shuttle`
   2. Copy the generated `shuttle.exe` (for a zip: all its files) into `C:\Program Files\Shuttle`
   3. Copy the [shuttle_task.vbs](/sdc_view/main_app/download/file_exporter_task.vbs) into the startup directory.  
      **Hint:** Press **Windows Key + R**, type `shell:startup`, and press Enter.

4. **(Special case) Install Shuttle with SFTP on Windows XP:**  
   The downloaded zip file `shuttle_sftp_winxp.zip` contains the executable and WinSCP.  
   1. Make a directory: `C:\Program Files\Shuttle`
   2. Unzip the file and copy **all** files (`shuttle.exe`, `WinSCP.exe`, `WinSCP.com`, `license.txt`) into `C:\Program Files\Shuttle`. WinSCP must stay next to `shuttle.exe`.
   3. Copy the [shuttle_task.vbs](/sdc_view/main_app/download/file_exporter_task.vbs) into the startup directory (see above).

5. **Install Shuttle on Linux:**  
   Installation requires administrative rights and is designed for **systemd**. Set the optional field *Linux user* of the instance: it is the user whose home holds the working folder.  
   1. Make a directory: `/opt/Shuttle`
   2. Copy the `shuttle` executable (for a zip: all its files) into `/opt/Shuttle/` and make it executable.
   3. Use the **systemd unit** button of the instance in the Shuttle list to download `shuttle.service` (generic fallback: [shuttle.service](/sdc_view/main_app/download/shuttle.service)). If it contains `User=CHANGE_ME`, replace it with the Linux user. Copy it into `/etc/systemd/system/shuttle.service`, then run:  
      ```bash
      systemctl daemon-reload
      systemctl enable --now shuttle.service
      ```

Shuttle keeps its log (`shuttle_log.txt`), the list of sent files (`sent_register.json`) and `known_hosts` in `~/shuttle/shuttle_<name>/` (Windows: `%USERPROFILE%\shuttle\shuttle_<name>\`). On the first start it sends every stable file already in the source folder once; delete `sent_register.json` to send everything again.

## Security options

Each Shuttle instance has three optional settings that control how the server is verified:

- **SSH host key** (SFTP only): the fingerprint of the server, either `SHA256:...` (optionally with the WinSCP prefix such as `ssh-ed25519 255 `) or `MD5:aa:bb:...`. Get it from WinSCP (*Session > Server/Protocol Information*) or with `ssh-keyscan -p <port> <host> | ssh-keygen -lf -`. It applies to both SFTP destinations (main and converter), so they must be the same server. **Required for Windows XP with SFTP**, unless verification is disabled.
- **Server certificate** (WebDAV only): a PEM file for servers with a self-signed or private certificate. It is shipped as `server.crt` next to the executable, so the download becomes a zip file (`shuttle_<architecture>.zip`). On Windows XP it is the only way TLS is verified.
- **Disable verification (insecure)**: switches off TLS and SSH host key verification. Any user can set it. The instance list marks such instances with a red "Verification disabled" badge; SFTP instances without host key show a "No host key" hint (the key is trusted on first use). Use it only for tests.

## Shuttle version

The git instance list shows the Shuttle version of each checkout (read after "Reload"). The Shuttle list shows the version each instance was last built with ("not built yet" otherwise); the tooltip of the download button names the version of the active git instance.

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