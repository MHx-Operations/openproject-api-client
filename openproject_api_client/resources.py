import datetime

from typing import List

from openproject_api_client import apiclient


class GenericType:
    def __init__(self, json_object=None, datetime_fields=None, date_fields=None, debug=False):
        self.id = None
        self.__type = None

        if datetime_fields is None:
            datetime_fields = []

        if date_fields is None:
            date_fields = []

        # if we get an obj form decode, fill attribs
        if json_object:

            if debug:
                # attach json for debugging
                self.json = json_object

            for k in json_object.keys():
                if k == '_type':
                    self.__type = json_object[k]

                if debug or (not k.startswith('_')):
                    if k.lower() in datetime_fields:
                        setattr(self, k.lower(), self.__parse_datetime(json_object[k]))
                    elif k.lower() in date_fields:
                        setattr(self, k.lower(), self.__parse_date(json_object[k]))
                    else:
                        setattr(self, k.lower(), json_object[k])

    def __str__(self):
        return f"GenericType({self.id}): type: {self.__type}"

    @staticmethod
    def __parse_datetime(val):
        if val:
            try:
                dt = datetime.datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                dt = val
        else:
            dt = val

        return dt

    @staticmethod
    def __parse_date(val):
        if val:
            try:
                dt = datetime.datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                dt = val
        else:
            dt = val

        return dt


class Project(GenericType):
    def __init__(self, json_object=None):
        self.id = 0
        self.identifier = ''
        self.name = ''
        self.active = False
        self.public = False
        self.description = None
        self.createdat = None
        self.updatedat = None
        self.status = None
        self.statusexplanation = None
        self.parent_id = None

        self.path = []
        self.path_ids = []
        self.level = 1
        self.fullname = ''

        super().__init__(json_object, datetime_fields=['createdAt', 'updatedAt'])

        # check for parentId
        if '_embedded' in json_object:
            if 'parent' in json_object['_embedded']:
                self.parent_id = json_object['_embedded']['parent']['id']

        if '_links' in json_object:
            if 'parent' in json_object['_links']:
                if json_object['_links']['parent']['href']:
                    if json_object['_links']['parent']['href'] != "urn:openproject-org:api:v3:undisclosed":
                        try:
                            self.parent_id = int(json_object['_links']['parent']['href'].split("/")[-1])
                        except:
                            # ok if unparseable
                            pass

    def __str__(self):
        return f"Project({self.id}): {self.name}"


class WorkPackage(GenericType):
    def __init__(self, json_object=None):

        self.createdat = None
        self.derivedduedate = None
        self.derivedestimatedtime = None
        self.derivedstartdate = None
        self.description = None
        self.duedate = None
        self.estimatedtime = None
        self.id = None
        self.lockversion = None
        self.percentagedone = None
        self.schedulemanually = None
        self.startdate = None
        self.subject = ''
        self.updatedat = None

        # attribs from embedd
        self.type = None
        self.type_id = None
        self.priority = None
        self.status = None
        self.status_id = None
        self.project = None
        self.project_id = None
        self.author = None
        self.author_id = None
        self.author_type = None
        self.assignee = None
        self.assignee_id = None
        self.assignee_type = None
        self.responsible = None
        self.responsible_id = None
        self.responsible_type = None
        self.version = None
        self.version_id = None

        # attribs from links
        self.parent_id = None

        # relations
        self.relations_obj: List[Relation] = []
        self.relations_out = {}
        self.relations_in = {}

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat', 'startdate', 'duedate'])

        if '_links' in json_object:
            if 'parent' in json_object['_links']:
                if json_object['_links']['parent']['href']:
                    self.parent_id = int(json_object['_links']['parent']['href'].split("/")[-1])

            if 'type' in json_object['_links']:
                if json_object['_links']['type']['href']:
                    self.type = json_object['_links']['type']['title']
                    self.type_id = int(json_object['_links']['type']['href'].split("/")[-1])

            if 'priority' in json_object['_links']:
                if json_object['_links']['priority']['href']:
                    self.priority = json_object['_links']['priority']['title']

            if 'status' in json_object['_links']:
                if json_object['_links']['status']['href']:
                    self.status = json_object['_links']['status']['title']
                    self.status_id = int(json_object['_links']['status']['href'].split("/")[-1])

            if 'project' in json_object['_links']:
                if json_object['_links']['project']['href']:
                    self.project = json_object['_links']['project']['title']
                    self.project_id = int(json_object['_links']['project']['href'].split("/")[-1])

            if 'author' in json_object['_links']:
                if json_object['_links']['author']['href']:
                    self.author = json_object['_links']['author']['title']
                    self.author_id = int(json_object['_links']['author']['href'].split("/")[-1])
                    self.author_type = json_object['_links']['author']['href'].split("/")[-2]

            if 'assignee' in json_object['_links']:
                if json_object['_links']['assignee']['href']:
                    self.assignee = json_object['_links']['assignee']['title']
                    self.assignee_id = int(json_object['_links']['assignee']['href'].split("/")[-1])
                    self.assignee_type = json_object['_links']['assignee']['href'].split("/")[-2]

            if 'responsible' in json_object['_links']:
                if json_object['_links']['responsible']['href']:
                    self.responsible = json_object['_links']['responsible']['title']
                    self.responsible_id = int(json_object['_links']['responsible']['href'].split("/")[-1])
                    self.responsible_type = json_object['_links']['responsible']['href'].split("/")[-2]

            if 'version' in json_object['_links']:
                if json_object['_links']['version']['href']:
                    self.version = json_object['_links']['version']['title']
                    self.version_id = int(json_object['_links']['version']['href'].split("/")[-1])

        if '_embedded' in json_object:
            if 'type' in json_object['_embedded']:
                self.type = json_object['_embedded']['type']['name']

            if 'priority' in json_object['_embedded']:
                self.priority = json_object['_embedded']['priority']['name']

            if 'status' in json_object['_embedded']:
                self.status = json_object['_embedded']['status']['name']

            if 'project' in json_object['_embedded']:
                self.project = json_object['_embedded']['project']['name']
                self.project_id = json_object['_embedded']['project']['id']

            if 'author' in json_object['_embedded']:
                self.author = json_object['_embedded']['author']['name']
                self.author_id = json_object['_embedded']['author']['id']

            if 'assignee' in json_object['_embedded']:
                self.assignee = json_object['_embedded']['assignee']['name']
                self.assignee_id = json_object['_embedded']['assignee']['id']

            if 'responsible' in json_object['_embedded']:
                self.responsible = json_object['_embedded']['responsible']['name']
                self.responsible_id = json_object['_embedded']['responsible']['id']

            if 'version' in json_object['_embedded']:
                self.version = json_object['_embedded']['version']['name']
                self.version_id = json_object['_embedded']['version']['id']

            if 'relations' in json_object['_embedded']:
                relations = json_object['_embedded']['relations']['_embedded']['elements']

                for relation in relations:
                    self.relations_obj.append(Relation(json_object=relation))

                self._calculate_relations_inout()

    def __str__(self):
        return f"WorkPackage({self.id}): {self.type} {self.subject}"

    def _calculate_relations_inout(self):
        self.relations_out = {}
        self.relations_in = {}

        # walk over relations to build relation by direction
        for r in self.relations_obj:
            # outbound relation
            if r.from_id == self.id:
                # create if node of type does not exists
                if r.type not in self.relations_out:
                    self.relations_out[r.type] = []

                self.relations_out[r.type].append(r.to_id)

            # inbound relation
            if r.to_id == self.id:
                # create if node of type does not exists
                if r.type not in self.relations_in:
                    self.relations_in[r.reversetype] = []

                self.relations_in[r.reversetype].append(r.from_id)

    def update_relations(self, relations=None) -> None:
        """
        updates relation_objs by providing relations externally using argument
        any relations affecting this workpackge is used and attached.
        relations_in and relations_out are also set accordingly.

        use this function when fetching workpackage in bluk i.e. queries or
        by project. fetching that way will NOT include relation information so
        you have to use this function to add relation information when needed

        :param relations: all relations objects, method filters by itself
        :type relations: List[Relation]
        """
        if relations is None:
            relations = []

        if relations:
            self.relations_obj = [r for r in relations if r.to_id == self.id or r.from_id == self.id]

        self._calculate_relations_inout()


class Relation(GenericType):
    def __init__(self, json_object=None):
        self.id = None
        self.description = None
        self.name = None
        self.reversetype = None
        self.type = None
        self.from_id = None
        self.from_title = ''
        self.to_id = None
        self.to_title = ''

        super().__init__(json_object, debug=False)

        if '_links' in json_object:
            if 'from' in json_object['_links']:
                if json_object['_links']['from']['href']:
                    self.from_id = int(json_object['_links']['from']['href'].split("/")[-1])
                    self.from_title = json_object['_links']['from']['title']

            if 'to' in json_object['_links']:
                if json_object['_links']['to']['href']:
                    self.to_id = int(json_object['_links']['to']['href'].split("/")[-1])
                    self.to_title = json_object['_links']['to']['title']

    def __str__(self):
        return f"Relation({self.id}): {self.from_id} -[{self.type}]-> {self.to_id}"


class Version(GenericType):
    def __init__(self, json_object=None):
        self.id = None
        self.createdat = None
        self.description = None
        self.enddate = None
        self.name = None
        self.sharing = None
        self.startdate = None
        self.status = None
        self.updatedat = None

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat'],
                         date_fields=['enddate', 'startdate'])

        # if '_links' in json_object:
        #     if 'from' in json_object['_links']:
        #         if json_object['_links']['from']['href']:
        #             self.from_id = int(json_object['_links']['from']['href'].split("/")[-1])
        #             self.from_title = json_object['_links']['from']['title']
        #
        #     if 'to' in json_object['_links']:
        #         if json_object['_links']['to']['href']:
        #             self.to_id = int(json_object['_links']['to']['href'].split("/")[-1])
        #             self.to_title = json_object['_links']['to']['title']

    def __str__(self):
        return f"Version({self.id}): {self.name}"

class User(GenericType):
    def __init__(self, json_object=None):
        self.id = None
        self.login = None
        self.firstname = None
        self.lastname = None
        self.name = None
        self.email = None
        self.createdAt = None
        self.updatedat = None

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat'],
                         date_fields=['enddate', 'startdate'])

        # if '_links' in json_object:
        #     if 'from' in json_object['_links']:
        #         if json_object['_links']['from']['href']:
        #             self.from_id = int(json_object['_links']['from']['href'].split("/")[-1])
        #             self.from_title = json_object['_links']['from']['title']
        #
        #     if 'to' in json_object['_links']:
        #         if json_object['_links']['to']['href']:
        #             self.to_id = int(json_object['_links']['to']['href'].split("/")[-1])
        #             self.to_title = json_object['_links']['to']['title']

    def __str__(self):
        return f"User({self.id}): {self.name}"

class PlaceholderUser(GenericType):
    def __init__(self, json_object=None):
        self.id = None
        self.name = None
        self.createdAt = None
        self.updatedat = None

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat'],
                         date_fields=[])

    def __str__(self):
        return f"PlaceholderUser({self.id}): {self.name}"

class Membership(GenericType):
    def __init__(self, json_object=None):
        self.id = None

        self.project = None
        self.project_id = None

        self.principal = None
        self.principal_id = None
        self.principal_type = None

        self.createdAt = None
        self.updatedat = None

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat'],
                         date_fields=[])

        if 'project' in json_object['_links']:
            if json_object['_links']['project']['href']:
                self.project = json_object['_links']['project']['title']
                self.project_id = int(json_object['_links']['project']['href'].split("/")[-1])

        if 'principal' in json_object['_links']:
            if json_object['_links']['principal']['href']:
                self.principal = json_object['_links']['principal']['title']
                self.principal_id = int(json_object['_links']['principal']['href'].split("/")[-1])
                self.principal_type = json_object['_links']['principal']['href'].split("/")[-2]


    def __str__(self):
        return f"Membership({self.id}): {self.name}"

class Status(GenericType):
    def __init__(self, json_object=None):
        self.id = None

        self.name = None
        self.color = None
        self.isclosed = None
        self.position = None

        self.createdAt = None
        self.updatedat = None

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat'],
                         date_fields=[])
    def __str__(self):
        return f"Status({self.id}): {self.name}"

class Version(GenericType):
    def __init__(self, json_object=None):
        self.id = None

        self.name = None
        self.startdate = None
        self.enddate = None
        self.status = None

        self.createdAt = None
        self.updatedat = None

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat'],
                         date_fields=[])
    def __str__(self):
        return f"Version({self.id}): {self.name}"

class Grid(GenericType):
    def __init__(self, json_object=None):
        self.id = None
        self.columncount = None
        self.createdat = None
        self.name = None
        self.options = None
        self.rowcount = None
        self.updatedat = None
        self.widgets = []

        self.scope = ''

        super().__init__(json_object, debug=False, datetime_fields=['createdat', 'updatedat'])

        if '_links' in json_object:
            if 'scope' in json_object['_links']:
                if json_object['_links']['scope']['href']:
                    self.scope = json_object['_links']['scope']['href']

        # parse widgets
        if isinstance(self.widgets, list):
            try:
                objs = []
                for w in self.widgets:
                    o = apiclient.ApiClient.decode(w)
                    objs.append(o)
                self.widgets = objs
            except apiclient.ApiError:
                pass

    def __str__(self):
        return f"Grid({self.id}): {self.scope} {self.name}"


class GridWidget(GenericType):
    def __init__(self, json_object=None):
        self.id = None
        self.endcolumn = None
        self.endrow = None
        self.identifier = None
        self.options = None
        self.startcolumn = None
        self.startrow = None

        super().__init__(json_object, debug=False)

    def __str__(self):
        return f"GridWidget({self.id}): {self.identifier} [({self.startcolumn},{self.startrow}) -> ({self.endcolumn},{self.endrow})]"


class Query(GenericType):
    def __str__(self):
        return f"Query({self.id}): {self.name}"

    def __init__(self, json_object=None):
        self.id = None
        self.createdat = None
        self.filters = None
        self.hidden = None
        self.highlightingmode = None
        self.name = None
        self.public = None
        self.showhierarchies = None
        self.starred = None
        self.sums = None
        self.timelinelabels = None
        self.timelinevisible = None
        self.timelinezoomlevel = None
        self.updatedat = None

        self.project = None
        self.project_id = None
        self.user = None
        self.user_id = None

        self.results = None

        super().__init__(json_object, debug=True, datetime_fields=['createdat', 'updatedat'])

        if 'project' in json_object['_links']:
            if json_object['_links']['project']['href']:
                self.project = json_object['_links']['project']['title']
                self.project_id = int(json_object['_links']['project']['href'].split("/")[-1])

        if 'user' in json_object['_links']:
            if json_object['_links']['user']['href']:
                self.user = json_object['_links']['user']['title']
                self.user_id = int(json_object['_links']['user']['href'].split("/")[-1])

        if '_embedded' in json_object:
            if 'results' in json_object['_embedded']:
                try:
                    self.results = apiclient.ApiClient.decode(json_object['_embedded']['results'])
                except:
                    self.results = json_object['_embedded']['results']


class Collection(GenericType):
    # https://thispointer.com/python-how-to-make-a-class-iterable-create-iterator-class-for-it/

    def __init__(self, json_object=None):
        self._items = None
        self.count = None
        self.offset = None
        self.pagesize = None
        self.total = None

        if '_embedded' in json_object:
            if 'elements' in json_object['_embedded']:
                elements = json_object['_embedded']['elements']

                try:
                    items = []
                    for element in elements:
                        items.append(apiclient.ApiClient.decode(element))
                    self._items = items

                except apiclient.ApiError:
                    self._items = elements

        super().__init__(json_object)

    def __iter__(self):
        return iter(self._items)

    def __str__(self):
        return f"{self.__class__.__name__}: count={self.count} total={self.total}"


class WorkPackageCollection(Collection):
    pass
