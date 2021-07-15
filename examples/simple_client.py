import os
import openproject_api_client as opc
import openproject_api_client.resources as res


class ShellColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


client = opc.ApiClient(os.environ.get('OPENPROJECT_BASEURL'), os.environ.get('OPENPROJECT_APIKEY'))

# projects
# #################################################################

print(f"{ShellColors.OKGREEN}fetching all projects from server{ShellColors.ENDC}")
projects_dict = client.get_projects_dict()
# projects = client.get_projects()

print(f"{ShellColors.OKBLUE}print all projects sorted by full name/hierarchy:{ShellColors.ENDC}")
for project in sorted(projects_dict.values(), key=lambda o: o.fullname):
    print("{} (id:{})".format(project.fullname, project.id))

print(f"{ShellColors.OKBLUE}print projects of a specific subtree, i.e. 54 (Innovations):{ShellColors.ENDC}")
filterId = 54
for project in [p for p in projects_dict.values() if filterId in p.path_ids]:
    print("{}".format(project.fullname))

# workpackages
# #################################################################

wps = client.get_workpackages_by_project_id(46)

try:
    wp = wps.pop()

    print(f"took first workpackage from project... {wp}")

    # get some details by making a explicit request
    # wp = client.get_workpackage(1155)
    wp = client.get_workpackage(wp.id)

    print(f"printing inbound relations {wp.relations_in}")
    print(f"printing outbound relations {wp.relations_out}")

except:
    print("no workpackage in this project found")
    pass

print(f"{ShellColors.OKBLUE}now print the rest of workpackages in the project:{ShellColors.ENDC}")
for wp in wps:
    print(wp)

print(f"{ShellColors.OKBLUE}fetch workpackages of query_id 12:{ShellColors.ENDC}")
wps = client.get_workpackages_by_query_id(12)
for wp in wps:
    print(wp)

# relations
# #################################################################

print(f"{ShellColors.OKBLUE}fetching all relations from server:{ShellColors.ENDC}")

relations = client.get_relations()
print (f"got {len(relations)} relations")
try:
    relation = relations.pop()
    print(f"took first relation: {relation}")

except:
    print("no relation found")
    pass

# versions
# #################################################################

print(f"{ShellColors.OKBLUE}fetching all relations from versions:{ShellColors.ENDC}")

versions = client.get_versions()
print (f"got {len(versions)} versions")

# version = client.get_version(27)
try:
    version = versions.pop()
    print(f"took first version: {version}")

except:
    print("no version found")
    pass

# grids a.k.a boards
# #################################################################

print(f"{ShellColors.OKBLUE}fetching all grids from versions:{ShellColors.ENDC}")

# grids = client.get_grids()
grids = client.get_grids(scope='/projects/yourproject/boards')

try:
    grid = grids.pop()
    print(f"took first grid: {grid}")

except:
    print("no grid found")
    pass

# fetch grid by ID
grid = client.get_grid(80)
if grid:
    print (f"looking inside grid {grid}")
    try:
        widget = grid.widgets[1] # get widget
        if widget:
            query_id = int(widget.options['queryId'])

        query = client.get_query(query_id)
        print (f"widget {widget} contains query {query}, you could manipulate or fetch workpackages via get_workpackages_by_query_id()")

    except:
        print ("some error fetching grid widget")



# trying raw get access
# #################################################################
if False:
    # access a single project
    p = client.get('projects/14')
    print(p)

    p = client.get('projects')
    print(p)

    # workpackage
    w = client.get('work_packages/362')
    print(w)

    # some debug sandbox
    tmp = client.get_query(20)
    tmp = client.get_workpackages_by_query_id(20)
    tmp = client.get_workpackages_by_query_id(12)

    tmp = client.get('projects/46/work_packages')
    tmp = client.get('grids')
    tmp = client.get('queries')
    tmp = client.get('queries/112')
