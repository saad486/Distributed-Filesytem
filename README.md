# Distributed-Filesytem

This is a distributed file sharing software and its aim is to provide a single filesystem image to any client connected to it.

# Installation
Config file of both server and client is provided. For now, support of three servers is provided in the code. A little tweak in code will make it accessible of more than three.

Server config : Write down the IPs of three servers (including the host)
Default port is chosen as 9999 for server to server communication. 
Chose the file path which is to be shared.

Client config: Write down the ip of server from which you have connect your client.
6666 is the default port.

Commands supported:
ls: to list all the files.
delete 'File': to delete the file
upload 'File': to upload the file
download 'File' : to download the file
create 'File' : to create a file

Python3 is used for coding and its environment is needed for running the code. This code is strictly for Linux file system and windows support is not given.




