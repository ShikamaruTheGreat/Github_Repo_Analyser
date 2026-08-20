setup instructions:
- this is not a deployed site, so
  1. if you wanna just test the endpoints, run main.py, use httpx in python for 127.0.0.1 on port 8000 + the endpoint to send requests, no authentication or jwt is required to access the endpoints, you can also use postman
  2. if you wanna use the web gui for this, run frontend.py, then go to your browser, put in 127.0.0.1/frontend/{endpoint}
  3. to use the application, you'll specifically need the web url for a github repository, this project can only read python files and ignores files ending with suffixes beside .py
  4. in the repo_analyser route, when you hit the analyse button, it'll give you a summary of A. the total and average assignments, ifs, function definitions etc. in each file B. the python code files sorted from highest linecount to lowest each
  5. you can also search from a collection of these repository statistics that have been uploaded to a database when a person uses the repo_analyser route
  Heads up: I still haven't implemented the mechanism where if a repository has no python files it skips any further operations like saving to the database (sorry)

Regarding the backend, I coded this myself (that's why its pretty buggy, the ast counts don't work much in some repos), first it was just the repo_analyser function with the logic_counter function, using python's ast's class to count the components of code, for each python file in the repository, then i discovered that the folder structure of most repos don't allow me to just read them, i gotta "cd" multiple layers to get each file, so i was like fuck that, i made a recursive algorithm that 
if a repository has subdirectories, each subdirectory gets unpacked and deleted, and if there were subdirectories within them, then they also get unpacked and deleted in the next function call, until (base case), all things in the repo directory are bare files

However, in doing this, .git was just making the algorithm not work for some reason, maybe it was because of the special files that were only one thing from read, write or execute, but i'm not sure, so i just hardcoded it to avoid that subdirectory like the plague

After that, setting up the database, selecting from it and the repo_search function was pretty straightforward, 

\
Regarding the frontend using NiceGUI, I basically vibecoded it, so I don't take any credit for it, cause I don't know CSS or the Quasar JS framework it uses under the hood.
