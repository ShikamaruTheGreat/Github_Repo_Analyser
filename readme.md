Regarding the backend, I coded this myself (that's why its pretty buggy, the ast counts don't work much in some repos), first it was just the repo_analyser function with the logic_counter function, using python's ast's class to count the components of code, for each python file in the repository, then i discovered that the folder structure of most repos don't allow me to just read them, i gotta "cd" multiple layers to get each file, so i was like fuck that, i made a recursive algorithm that 
if a repository has subdirectories, each subdirectory gets unpacked and deleted, and if there were subdirectories within them, then they also get unpacked and deleted in the next function call, until (base case), all things in the repo directory are bare files

However, in doing this, .git was just making the algorithm not work for some reason, maybe it was because of the special files that were only one thing from read, write or execute, but i'm not sure, so i just hardcoded it to avoid that subdirectory like the plague

After that, setting up the database, selecting from it and the repo_search function was pretty straightforward, 

\
Regarding the frontend using NiceGUI, I basically vibecoded it, so I don't take any credit for it, cause I don't know CSS or the Quasar JS framework it uses under the hood.