#!/usr/bin/python

#_________________________________________________________________________
#| Copyright 2014 GHOSTnew                                               |
#|_______________________________________________________________________|
#| This program is free software: you can redistribute it and/or modify  |
#| it under the terms of the GNU General Public License as published by  |
#| the Free Software Foundation, either version 3 of the License, or     |
#| any later version.                                                    |
#|                                                                       |
#| This program is distributed in the hope that it will be useful,       |
#| but WITHOUT ANY WARRANTY; without even the implied warranty of        |
#| MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         |
#| GNU General Public License for more details.                          |
#|                                                                       |
#| You should have received a copy of the GNU General Public License     |
#| along with this program.  If not, see <http://www.gnu.org/licenses/>. |
#|_______________________________________________________________________|

import socks
import socket
import ConfigParser
import thread
import time
import ssl

def send_to_peers():
    while True:
        error = 0
        peers_conf = ConfigParser.ConfigParser()
        peers_conf.read('conf/peers.ini')
        for i in range(len(peers_conf.sections())):
            if peers_conf.getboolean(peers_conf.sections()[i], 'Tor'):
                socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
            else:
                socks.setdefaultproxy()
            socket.socket = socks.socksocket
            s = socket.socket()
            try:
                s.connect((peers_conf.get(peers_conf.sections()[i], 'host'), peers_conf.getint(peers_conf.sections()[i], 'port')))
                hostlist = open("conf/host.txt", "r")
                for ligne in hostlist:
                    s.send(ligne)
                hostlist.close()
                s.close()
            except:
                s.close()
                print "\0034connexion impossible"
                error = error +1
            i=i+1
        if error == len(peers_conf.sections()): 
            print "Error aucun pair disponible"
        error = 0
        time.sleep(3600)
       
def recv_host():
    toute_data = []
    host_tab = []
    global_conf = ConfigParser.ConfigParser()
    global_conf.read('conf/global.ini')
    lsock = socket.socket()
    lsock.bind((global_conf.get('router', 'ip'), global_conf.getint('router', 'port')))
    lsock.listen(5)
    while True:
        client, (remhost, remport) = lsock.accept()
        while True:
            data = client.recv(1024)
            print data
            if not data:
               break
            toute_data.append(data.replace('\n','').replace('\r', ''))
        fichier = open("conf/host.txt", "r")
        lignes = fichier.readlines()
        x = 0
        for d in toute_data:
            found = False
            for l in lignes:
                if d == l.replace("\n", ""):
                    found = True
            if found:
                host_tab.append(l)
            else:
                host_tab.append(d + "\n")
        for l in lignes:
            found = False
            for d in toute_data:
                if d == l.replace("\n", ""):
                    found = True
            if not found:
                host_tab.append(l)
        fichier.close
        fichier = open("conf/host.txt", "w")
        a = ""
        for l in host_tab:
            a += l
        fichier.write(a)
        host_tab = []
        toute_data = []
        fichier.close()
        client.close()

def proxy():
    global_conf = ConfigParser.ConfigParser()
    global_conf.read('conf/global.ini')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((global_conf.get('proxy', 'ip'),  global_conf.getint('proxy', 'port')))
    s.listen(30)
    while 1:
        conn, client_addr = s.accept()
        thread.start_new_thread(proxy_thread, (conn, client_addr))
    s.close()

def proxy_thread(conn, client_addr):
    request = conn.recv(4096)
    first_line = request.split('\n')[0]
    url = first_line.split(' ')[1]
    http_pos = url.find("://")
    if (http_pos==-1):
        temp = url
    else:
        temp = url[(http_pos+3):]
    port_pos = temp.find(":")
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)
    webserver = ""
    port = -1
    if (port_pos==-1 or webserver_pos < port_pos):
        port = 80
        webserver = temp[:webserver_pos]
    else:
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos] 
    host_existe = False
    if webserver.__contains__(".f2f"):
        host_serv = ''
        fichier = open("conf/host.txt", "r")
        for ligne in fichier:
            if ligne.split(" ")[0] == webserver:
                host_serv = ligne.split(" ")[1].split("\n")[0]
                host_existe = True
        fichier.close()
        if host_existe:
            global_conf = ConfigParser.ConfigParser()
            global_conf.read('conf/global.ini')
            if global_conf.getboolean('proxy', 'Tor'):
                socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
            else:
                socks.setdefaultproxy()
            socket.socket = socks.socksocket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                s.connect((host_serv, port))
                if port == 443 or port == 6697:
                    try:
                        s = ssl.wrap_socket(s)
                        s.tsock.do_handshake()
                    except:
                        print "[-] Failed to do ssl handshake"

                s.send(request)
 
                while 1:
                    data = s.recv(4096)
            
                    if data:
                        print data
                        conn.send(data)
                    else:
                        break
                s.close()
                conn.close()
            except socket.error, (value, message):
                if s:
                    s.close()
                if conn:
                    conn.close()
                print "Runtime Error:", message
        else:
            fichier = open("conf/error/404.html")
            error = ""
            for line in fichier:
                line = line.replace("{{domaine}}", webserver)
                error += line
            result = """HTTP/1.1 404 NOT FOUND\r
Upgrade: WebSocket\r
Connection: Upgrade\r
Content-Type: text/html; charset=utf-8""".strip() + '\r\n\r\n' + "\x00"+ error
            print result
            conn.send(result)
            conn.close()
    else:
        fichier = open("conf/error/500.html")
        error = ""
        for line in fichier:
            line = line.replace("{{domaine}}", webserver)
            error += line
        result = """HTTP/1.1 500 internal server error\r
Upgrade: WebSocket\r
Connection: Upgrade\r
Content-Type: text/html; charset=utf-8""".strip() + '\r\n\r\n' + "\x00"+ error
        print result
        conn.send(result)
        conn.close()

if __name__ == "__main__":
    thread.start_new_thread(send_to_peers, ())
    thread.start_new_thread(recv_host, ())
    proxy()
