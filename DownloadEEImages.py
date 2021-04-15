#Code by Jake Slyder, jslyder@blm.gov.  Download function adapted from code by Yann Forget.
#Code should be run in Python 3, but uses fairly standard packages.
#Script requires machine to machine access to your EarthExplorer account.

#Last update March 10, 2021

import re
import ast
import os
import sys
import time
import json
import requests
from builtins import input
from datetime import datetime


if sys.version_info[0] == 2:
    from Tkinter import *
    import tkFileDialog as fdialog
    import ttk
    #r = raw_input('Paste your query response from EE API page')
else:
    from tkinter import *
    import tkinter.filedialog as fdialog
    from tkinter import ttk as ttk
    #r = input('Paste your query response from EE API page')


#Define the necessary stand-alone functions
def download(url, output_dir, replace=True, chunk_size=1024):
    """Download remote file given its URL."""
    r = requests.get(url, stream=True, allow_redirects=True)
    #print(re.findall(r'<a href="(.*?)" title="\1"', r.text))
    #local_filename = getFilename_fromCd(r.headers.get('content-disposition'))
    #print(r.json())
    #file_size = getFilename_fromCd(r.headers.get('content-length'))
    #file_size = int(r.headers['Content-Length'])
    file_size = int(r.headers.get("Content-Length"))
    local_filename = r.headers['Content-Disposition'].split('=')[-1]
    local_filename = local_filename.replace("\"", "")
    local_filename = os.path.join(output_dir, local_filename)
    print(file_size,local_filename)
    if os.path.exists(local_filename) and not replace:
        print("Skipping file that exists: %s" %local_filename)
    else:

        #print("Source is Basket")
        listItemProgBar['maximum'] = file_size
        iprogbask = 0
        listItemProgBar['value'] = iprogbask
        listItemProgBar.update()

        c = 0
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    #print("test %s"%c)
                    f.write(chunk)
                    c+=1
                iprogbask += chunk_size
                listItemProgBar['value'] = iprogbask
                listItemProgBar.update()

    del r
    return local_filename

#Create the appliation class
class EEDownloader(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        #Change the window title
        self.title("BLM Earth Explorer Bulk Downloader")

        #Create label frame to hold all elements for logging in and populating label
        loginLF = ttk.LabelFrame(self,text="Login and Choose Order")

        #Create login credentials widgets
        label1 = ttk.Label(loginLF, text='Enter EarthExplorer Credentials Below', wraplength= 300)
        label2 = ttk.Label(loginLF, text='Username')
        label3 = ttk.Label(loginLF, text='Password')
        e1 = ttk.Entry(loginLF)
        e2 = ttk.Entry(loginLF, show="*")
        loginButton = ttk.Button(loginLF, text="Login", command=lambda: self.login(username=e1.get(),password=e2.get()))

        # Widgets for download label info
        #label4 = ttk.Label(loginLF, text='Order Label')
        global labelChoiceMenu
        labelChoice = StringVar(self)
        labelChoiceMenu = ttk.OptionMenu(loginLF, labelChoice)
        labelChoiceMenu["state"] = "disabled"

        #Warning label, leave blank at first, populate and style from login method
        global wLabel
        wLabel = ttk.Label(loginLF, text='',width=30,wraplength=300,anchor="center")
        
        

        #Add the widgets to the login label frame
        label1.grid(row=0, columnspan=2)
        label2.grid(row=1, column = 0)
        label3.grid(row=2, column = 0)
        e1.grid(row=1, column = 1,sticky='we')
        e2.grid(row=2, column = 1,sticky='we')
        loginButton.grid(row=3,column=0,columnspan=2,sticky='we')
        #label4.grid(row=4, column = 0)
        labelChoiceMenu.grid(row=3, column = 2,sticky='we')
        wLabel.grid(row=0,column=2,rowspan=3,padx=(5,0))
   
        

        #Create and populate label frame with staging items
        stageLF = ttk.LabelFrame(self,text="Stage Bulk Order for Downloading")
        #Add the items to stage the download
        t = "EE orders must be staged for download.  Once your order is selected above, click the button below to start staging the order.  After staging, you can use the Check Order Status button to see how many items are available.  Note that large orders may take an hour or more to stage."
        stageText = ttk.Label(stageLF, text=t,wraplength=420)
        global stageButton
        stageButton = ttk.Button(stageLF, text="Stage Download", width=30,state="disabled",command=lambda: self.stageDL(label=labelChoice.get()))
        
        global stageLabel
        stageLabel = ttk.Label(stageLF, text='',width=30,anchor="center")

     
        
        global ordStatLabel
        ordStatLabel = ttk.Label(stageLF, text="")
        
        #button to check status
        global ordStatButton
        ordStatButton = ttk.Button(stageLF, text="Check Order Status", width=30,state="disabled", command=lambda: self.checkOrderStatus(label=labelChoice.get()))

        
        
        #Add items to a grid in the LF
        stageText.grid(row=0, columnspan=2)
        stageButton.grid(row=1,column=0,sticky='w')
        stageLabel.grid(row=1,column=1)
        
        
        #Add the widgets to the time lf
        ordStatButton.grid(row=2,column=0,sticky='w')
        ordStatLabel.grid(row=2,column=1)

        
        


        
        
        #Create label frame to hold all elements for creating download text file
        txtLF = ttk.LabelFrame(self,text="Create Download Text File")
        fileLab = ttk.Label(txtLF, text='Specify output text file', wraplength= 300)
        global outFile
        outFile = ttk.Entry(txtLF,width=35)
        fileBrowseButton = ttk.Button(txtLF, text='Set Output Text File', width=30, command=lambda: self.chooseOutputFile())
        global runTextButton
        runTextButton = ttk.Button(txtLF, text="Generate Text File Download List", width=30,state="disabled",command=lambda: self.toTxt(label=labelChoice.get(),outputFile=outFile.get()))

        #Add elements to the text file label frame
        fileLab.grid(row=8, columnspan=3, sticky='w')
        outFile.grid(row=9,column=0,columnspan=2, sticky='we')
        fileBrowseButton.grid(row=9,column=2,sticky='we')
        runTextButton.grid(row=10,column=2,sticky='we')

        #Create label frame to hold all elements for downloading imagery
        dlLF = ttk.LabelFrame(self,text="Download Imagery")
        #Check box to enable/disable overwriting files
        overwriteFiles = BooleanVar(self)
        check = ttk.Checkbutton(dlLF, text='Overwrite existing files?', variable=overwriteFiles)
        #Check box to also create text file
        writeTxt = BooleanVar(self)
        txtCheck = ttk.Checkbutton(dlLF, text='Write download text file to output directory as well?', variable=writeTxt)
        #Get the outpt directory to download directly
        dirLab = ttk.Label(dlLF, text='Specify Output Directory to Download Files', wraplength= 300)
        global listOutDir
        listOutDir = ttk.Entry(dlLF,width=35)
        #Buttons to browse for output directory as well as to run the process
        dirBrowseButton = ttk.Button(dlLF, text='Browse for Directory', width=30, command=lambda: self.chooseOutputDirectory())
        global listRunBut
        listRunBut = ttk.Button(dlLF, text='Run Download', 
                                width=30, state="disabled",
                                command=lambda: self.runSceneListDownload(label=labelChoice.get(), 
                                                                          out=listOutDir.get(), 
                                                                          overwrite=overwriteFiles.get(),
                                                                          txt = writeTxt.get()))

        #Add the widgets to the download label frame
        dirLab.grid(row=4, columnspan=3, sticky='w')
        listOutDir.grid(row=5, columnspan=2, sticky='we')
        dirBrowseButton.grid(row=5,column=2, sticky='we')
        txtCheck.grid(row=6, padx=1, pady=(5,5),columnspan=3, sticky='w')
        check.grid(row=7, padx=1, pady=(5,5), sticky='w')
        listRunBut.grid(row=7,column=2, sticky='we')


        #Create a label frame with instructions
        instLF = ttk.LabelFrame(self, text='Tool Instructions')
        instructions = '1. On Earth Explorer, create a bulk order as you normally would. Submit the order, noting the label if used.  \n\n2. In the top section to the left, enter your Earth Explorer login credentials and click login. On successful login, a list of your orders will appear to choose from.\n\n3.  If you have not yet done so, click the Stage Download button to start staging your order for downloading.  Staging for downloading can be a slow process, so you may wish to start staging and then return later to download.  You can use the Check Order Status button to determine if all items are available to download.  \n\n4. Fill out and run ONLY ONE of the sections at the bottom depending on if you want to create a text file for another download application (top) or you want to download through this tool (bottom, only recommended for small orders).  \n\nProgram by Jake Slyder.  Email screenshot of errors to jslyder@blm.gov'
        instText = Text(instLF, width = 60, borderwidth = 2, wrap=WORD)
        instText.insert(1.0, instructions)
        instText.configure(font=("Courier"))
        instText.config(state=DISABLED)
        instText.pack(padx=5,pady=5)

        #Add label frames to the grid of the main window
        loginLF.grid(row=3, columnspan = 3,sticky='we',padx=(5,1))
        stageLF.grid(row=5,columnspan=3,sticky='we',padx=(5,1))
        txtLF.grid(row=8, columnspan = 3,sticky='we',padx=(5,1))
        dlLF.grid(row=12, columnspan = 3,sticky='we',padx=(5,1))
        instLF.grid(row=3,column=3,rowspan=13,sticky='ns',padx=(10,5),pady=5)

        #Initiate variables for progress window stuff, but do not add to Grid
        #Starting the download process will add them to the grid
        #Progress window label
        global listProgLab
        listProgLab = ttk.Label(dlLF, text='Progress Window', wraplength= 300)
        #Add a progress message
        global listProgMsg
        listProgMsg = ttk.Label(dlLF, text='')
        # Add an ITEM progress bar label
        global listItemProgBarLab
        listItemProgBarLab = ttk.Label(dlLF, text='Progress Bar (item)')
        # Add an ITEM progress bar
        global listItemProgBar
        listItemProgBar = ttk.Progressbar(dlLF, orient='horizontal', mode='determinate')
        #Add a progress bar label
        global listProgBarLab
        listProgBarLab = ttk.Label(dlLF, text='Progress Bar (overall order)')
        #Add a progress bar
        global listProgBar
        listProgBar = ttk.Progressbar(dlLF, orient = 'horizontal',mode = 'determinate')

#Define methods for the applicaiton class

    #Log into EE, populate download list, get API key and add to headers variable for other functions
    def login(self,username,password):
          #r = '{ "requestId": 57616845, "version": "stable", "data": { "available": [ { "downloadId": 2810602, "collectionName": "Aerial Photo Single Frames", "datasetId": "5e83d8e4870f4473", "displayId": "AR4CO77B116N345", "entityId": "AR4CO77B116N345", "eulaCode": null, "filesize": 105595, "label": "js test 2", "productCode": "D555", "productName": "USGS CAMERA CALIBRATION REPORT DOWNLOAD", "statusCode": "A", "statusText": "Available", "url": "https://dds.cr.usgs.gov/download/eyJpZCI6MjgxMDYwMiwiY29udGFjdElkIjoxNDM4NDQ3fQ==" }, { "downloadId": 2810604, "collectionName": "Aerial Photo Single Frames", "datasetId": "5e83d8e4870f4473", "displayId": "AR5880037725689", "entityId": "AR5880037725689", "eulaCode": null, "filesize": 40778242, "label": "js test 2", "productCode": "D197", "productName": "AERIAL PHOTO SINGLE FRAME MEDIUM RESOLUTION DOWNLOAD", "statusCode": "A", "statusText": "Available", "url": "https://dds.cr.usgs.gov/download/eyJpZCI6MjgxMDYwNCwiY29udGFjdElkIjoxNDM4NDQ3fQ==" }, { "downloadId": 2810603, "collectionName": "Aerial Photo Single Frames", "datasetId": "5e83d8e4870f4473", "displayId": "AR5880037725688", "entityId": "AR5880037725688", "eulaCode": null, "filesize": 40777102, "label": "js test 2", "productCode": "D197", "productName": "AERIAL PHOTO SINGLE FRAME MEDIUM RESOLUTION DOWNLOAD", "statusCode": "A", "statusText": "Available", "url": "https://dds.cr.usgs.gov/download/eyJpZCI6MjgxMDYwMywiY29udGFjdElkIjoxNDM4NDQ3fQ==" }, { "downloadId": 2810605, "collectionName": "Aerial Photo Single Frames", "datasetId": "5e83d8e4870f4473", "displayId": "AR5880037725690", "entityId": "AR5880037725690", "eulaCode": null, "filesize": 40779242, "label": "js test 2", "productCode": "D197", "productName": "AERIAL PHOTO SINGLE FRAME MEDIUM RESOLUTION DOWNLOAD", "statusCode": "A", "statusText": "Available", "url": "https://dds.cr.usgs.gov/download/eyJpZCI6MjgxMDYwNSwiY29udGFjdElkIjoxNDM4NDQ3fQ==" }, { "downloadId": 2810606, "collectionName": "Aerial Photo Single Frames", "datasetId": "5e83d8e4870f4473", "displayId": "AR5880037725691", "entityId": "AR5880037725691", "eulaCode": null, "filesize": 40778886, "label": "js test 2", "productCode": "D197", "productName": "AERIAL PHOTO SINGLE FRAME MEDIUM RESOLUTION DOWNLOAD", "statusCode": "A", "statusText": "Available", "url": "https://dds.cr.usgs.gov/download/eyJpZCI6MjgxMDYwNiwiY29udGFjdElkIjoxNDM4NDQ3fQ==" } ], "queueSize": 0, "requested": [], "eulas": [] }, "errorCode": null, "errorMessage": null }'
        wLabel.configure(text="",foreground="black")

        catalog = 'EE'
        parameters = {
                    'username': username,
                    'password': password,
                    'authType': 'EROS',
                    'catalogId': catalog
                }
        parameters = json.dumps(parameters)
        r = requests.post('https://m2m.cr.usgs.gov/api/api/json/stable/login', data=parameters)
        #convert the response to json then to a string
        rStr = str(r.json())
        print(rStr)
        #extract the dictionary out of the string response
        d = ast.literal_eval(re.search('({.+})', rStr).group(0))

        #Grab the returned API key, put it in the header for get requests below.
        apiKey = d['data']
        print(apiKey)

        #If it returns none, as in there is a login error, address that here
        if apiKey is None:
            wLabel.configure(text="Login Failed!",foreground="red")
            return

        global headers
        headers = {'X-Auth-Token': apiKey}

        #First try to run the command to get a list of labels
        parameters = {
                    'activeOnly': 'true'
                }
        parameters = json.dumps(parameters)

        r = requests.get('https://m2m.cr.usgs.gov/api/api/json/stable/download-search', data=parameters, headers=headers)
        r = str(r.json())
        #print(r)
        d = ast.literal_eval(re.search('({.+})', r).group(0))
        orderLabels = []
        d = d['data']
        #print(d)

        for i in d:
            print(str(i)+"\n\n")
            #if i['label'] not in orderLabels and len(i['label'])<30:
            if i['label'] not in orderLabels and not i['label'].startswith('ee_'):
                orderLabels.append(i['label'])

        labelChoiceMenu["state"] = "normal"
        print(orderLabels)
        for o in orderLabels:
            labelChoiceMenu.set_menu(*orderLabels)
        wLabel.configure(text="Login Succesful! Choose\norder from list below.",anchor="center")
        stageButton["state"] = "normal"
        ordStatButton["state"] = "normal"
    
    #Create a function to start staging the download
    def stageDL(self,label):

        parameters = { "label": label, "downloadApplication": "BulkDownload" }
        parameters = json.dumps(parameters)
        r = requests.get('https://m2m.cr.usgs.gov/api/api/json/stable/download-order-load', data=parameters, headers=headers)
        r = str(r.json())
        print(r)

        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        lab = "Order Staged at {}.".format(current_time)
        stageLabel.configure(text=lab,foreground="black")
        self.checkOrderStatus(label)
    
    #method to check order status
    def checkOrderStatus(self,label):
        
        #Clear any existing text
        ordStatLabel.configure(text='',anchor="center")
        
        #first, use download retrieve to get the total number available
    
        parameters = { "label": label }
        parameters = json.dumps(parameters)
        r = requests.get('https://m2m.cr.usgs.gov/api/api/json/stable/download-retrieve', data=parameters, headers=headers)
        r = str(r.json())
        #print(r)
        
        #Make sure the null values are a string when the dictionary is extracted from the string
        r = r.replace("null",'"null"')
        #Extract the dictionary from the input string
        d = ast.literal_eval(re.search('({.+})', r).group(0))
        d = d['data']

        #Grab the available item in the data response
        a = d['available']
        avail = len(a)
           
        #Next, use the download summary function to get the total number of scenes 
        parameters = { "label": label,  "downloadApplication": "BulkDownload" }
        parameters = json.dumps(parameters)
        r = requests.get('https://m2m.cr.usgs.gov/api/api/json/stable/download-summary', data=parameters, headers=headers)
        r = str(r.json())
        #print(r)
        
        #Make sure the null values are a string when the dictionary is extracted from the string
        r = r.replace("null",'"null"')
        #Extract the dictionary from the input string
        d = ast.literal_eval(re.search('({.+})', r).group(0))
            
        print("\n\n\n")
        d = d['data']
        #print(d)
        #print("scene count")
        #print(d['sceneCount'])
        #l = d['available']
        statTxt = "{} of {} items available.".format(avail,d['downloadCount'])
        ordStatLabel.configure(text=statTxt,anchor="center")
        
        #Also update the status message
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        lab = "Status Checked at {}.".format(current_time)
        stageLabel.configure(text=lab,foreground="black")
    
    #Create a text file of download URLs for use in other download application
    def toTxt(self,label,outputFile):

        print(label)

        #Get request to retrieve download urls
        #Only parameter to be sent is the order label
        parameters = { "label": label }
        parameters = json.dumps(parameters)
        r = requests.get('https://m2m.cr.usgs.gov/api/api/json/stable/download-retrieve', data=parameters, headers=headers)
        r = str(r.json())
        print(r)


        #Create a list of download URLs
        dlURL = []

        #Make sure the null values are a string when the dictionary is extracted from the string
        r = r.replace("null",'"null"')
        #Extract the dictionary from the input string
        d = ast.literal_eval(re.search('({.+})', r).group(0))


        d = d['data']
        print(d)
        l = d['available']
        '''
        If you have already run a download-retrieve query then sometimes the items
        in an order are moved from "available" to "requested."  Therefore, I made
        a list out of each to iterate through.
        '''
        l2 = d['requested']

        #Iterate through responses to gather download URLs
        for i in l:
            if len(i['url']) > 5:
                dlURL.append(i['url'])
        for i in l2:
            if len(i['url']) > 5:
                dlURL.append(i['url'])

        print(dlURL)
        
        if len(dlURL) == 0: #if there are no available download urls
            #Acknowledge the successful end of the process
            top = Toplevel(app)
            Label(top, text='Warning! No downloads available.  Check order status.', anchor=W, justify=LEFT, wraplength= 300).grid(row=1, columnspan=2)
            top.mainloop()
            return
        else:

            #First check if there is an existing output text file.  If so, make a list of existing urls
            existingURLs = []
            if os.path.exists(outputFile):
                with open(outputFile) as fr:
                    eu = fr.read().splitlines()
                    for u in eu:
                        existingURLs.append(u)
                del fr
    
            #Next, write the urls returned from EE to the text file, first checking
            #to see if those URLs already exist in the text file
            with open(outputFile,"a") as f:
                # Further file processing goes here
                for i in dlURL:
                    if i not in existingURLs:
                        s = str(i)+"\n"
                        f.write(s)
            del f
    
            #Acknowledge the successful end of the process
            top = Toplevel(app)
            Label(top, text='Success!', anchor=W, justify=LEFT, wraplength= 300).grid(row=1, columnspan=2)
            top.mainloop()
            return

    #Paste from clipboard,used in earlier verasion
##    def paste(self, *args):
##        #Get the contents of the clipboard
##        clipboard = self.clipboard_get()
##        clipboard = clipboard.replace("\n", "\\n")
##        e3.delete(0, "end")
##        e3.insert(0, clipboard)

    #Methods below for choosing outputs
    def chooseOutputFile(self):
        f = fdialog.asksaveasfilename( defaultextension='.txt', filetypes=[("Text File", '*.txt')],title="Choose output filename")
        print(f)
        outFile.delete(0, "end")
        outFile.insert(0, f)
        if len(f) >0:
            runTextButton["state"] = "normal"

    def chooseOutputDirectory(self):
        f = fdialog.askdirectory(title="Choose output directory for download")
        print(f)
        listOutDir.delete(0, "end")
        listOutDir.insert(0, f)
        if len(f) >0:
            listRunBut["state"] = "normal"

    #Run the download process, and optionally build text file.
    def runSceneListDownload(self,label,out,overwrite,txt):

        #First, add the items to the bottom of the window to update status on downloads
        listProgLab.grid(row=10, columnspan=3, pady=(5,1), sticky='we')
        listProgMsg.grid(row=11, columnspan=2, pady=(5,1), sticky='w')
        listItemProgBarLab.grid(row=12, columnspan=2, pady=(5,1), sticky='w')
        listItemProgBar.grid(row=13, columnspan=3, padx=(5,1), pady=(2,5), sticky='we')
        listProgBarLab.grid(row=14, columnspan=2, pady=(5,1), sticky='w')
        listProgBar.grid(row=15, columnspan=3, padx=(5,1), pady=(2,5), sticky='we')
        listProgMsg.config(foreground="Black")



        #Get request to retrieve download urls
        #Only parameter to be sent is the order label
        parameters = { "label": label }
        parameters = json.dumps(parameters)
        r = requests.get('https://m2m.cr.usgs.gov/api/api/json/stable/download-retrieve', data=parameters, headers=headers)
        r = str(r.json())
        #print(r)


        #Create a dictionary for download URLs, use dict here to save entity ids
        dlURL = {}
        #make sure that the null values will remain as a string once converted back to dicintary
        r = r.replace("null",'"null"')
        #Extract the dictionary from the input string
        d = ast.literal_eval(re.search('({.+})', r).group(0))
        '''
        Grab the relevant data from the extracted dictionary.  If you have already
        run a download-retrieve query then sometimes the items in an order are
        moved from "available" to "requested."  Therefore, I made a list out of
        each to iterate through.
        '''
        d = d['data']
        l = d['available']
        l2 = d['requested']

        #Iterate through responses to gather download URLs
        for i in l:
            if len(i['url']) > 5:
                k = str(i["productCode"]) + "_" + str(i['entityId'])
                dlURL[k] = i['url']
        for i in l2:
            if len(i['url']) > 5:
                k = str(i["productCode"]) + "_" + str(i['entityId'])
                dlURL[k] = i['url']

        print(dlURL)
        #Update progress bar with total count of URLs, set current counter to 0
        listProgBar["maximum"] = len(dlURL)
        progCounter = 0
        listProgBar["value"] = progCounter
        listProgBar.update()

        #Create an error list for downloads where an issue is thrown.
        errorList =[]
        out = str(out).replace("/","\\")

        #If they choose to also write a text file, do that here.
        if txt:
            outputFile = os.path.join(out, "EEDownloadList.txt")
            #First check if there is an existing file.  If so, make a list of existing urls
            existingURLs = []
            if os.path.exists(outputFile):
                with open(outputFile) as fr:
                    eu = fr.read().splitlines()
                    for u in eu:
                        existingURLs.append(u)
                del fr

            #Next, write the urls to the text file, first checking to see if
            #they already exist in the text file
            if len(dlURL) > 0:
                with open(outputFile,"a") as f:
                # Further file processing goes here
                    for i in dlURL.keys():
                        if str(dlURL[i]) not in existingURLs:
                            s = str(dlURL[i])+"\n"
                            f.write(s)
                del f

        #Next, start the download process by iterating through dlURL
        for i in dlURL.keys():
            try:
                #Update text to indicate current item
                ci = progCounter
                ci += 1
                update="Current Item ({} of {}): {}".format(ci,len(dlURL),i)
                listProgMsg['text'] = update
                listProgMsg.update()
                #Send the command to download the current item
                download(url=dlURL[i], output_dir=out, replace=overwrite, chunk_size=1024)
                #Update the order progress bar
                progCounter+=1
                listProgBar["value"] = progCounter
                listProgBar.update()
            except Exception as e:
                print(e)
                errorList.append([i,dlURL[i]])
                #Even if an error is thrown, this item is considered complete,
                #so inrement the counter and update the order progress bar
                progCounter+=1
                listProgBar["value"] = progCounter
                listProgBar.update()

        #If errors were thrown and logged, iterate through that list to write
        #them to a text file.
        if len(errorList) > 0:
            outText = str(out) + "/ScenesWithDownloadErrors.txt"
            outf = open(outText,'w')
            outf.write("List of scenes that had download errors\n")
            for i in errorList:
                line = "%s\t%s\n"%(i[0],i[1])
                outf.write(line)
            outf.close()
            listProgMsg['text'] = "Download completed with errors.  See text file in output directory.\n"
        else:
            listProgMsg['text'] = "Download Complete"

#Run the program
if __name__ == "__main__":
    app = EEDownloader()
    #Lock the size of the widow
    app.resizable(width=False, height=False)
    app.mainloop()

