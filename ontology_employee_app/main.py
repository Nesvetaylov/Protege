from flask import Flask, render_template, request
import rdflib

app = Flask(__name__, template_folder='templates')

graph = rdflib.Graph()
graph.parse("lab_1.rdf", format="xml")

NS = rdflib.Namespace("http://www.semanticweb.org/xe/ontologies/2025/10/untitled-ontology-4#")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/projects', methods=['POST', 'GET'])
def get_projects():
    query = """
    PREFIX ns: <http://www.semanticweb.org/xe/ontologies/2025/10/untitled-ontology-4#>
    SELECT ?p ?name ?desc ?budget
    WHERE {
        ?p rdf:type ns:Project .
        OPTIONAL { ?p ns:hasName ?name . }
        OPTIONAL { ?p ns:hasDescription ?desc . }
        OPTIONAL { ?p ns:budget ?budget . }
    }
    """
    qres = graph.query(query)
    projects = []
    for row in qres:
        projects.append({
            "id": str(row.p).split('#')[-1],
            "name": str(row.name) if row.name else "Проект без названия",
            "desc": str(row.desc) if row.desc else "Описание отсутствует",
            "budget": str(row.budget) if row.budget else "Не указан"
        })
    return render_template('projects.html', projects=projects)

@app.route('/employees', methods=['POST', 'GET'])
def get_employees():
    query = """
    PREFIX ns: <http://www.semanticweb.org/xe/ontologies/2025/10/untitled-ontology-4#>
    SELECT ?emp ?name ?pos
    WHERE {
        ?emp rdf:type ns:Employee .
        
        OPTIONAL { ?emp ns:hasName ?name . }
        
        OPTIONAL { ?emp ns:Занимает_должность ?posObj . }
        
        BIND(STRAFTER(STR(?posObj), "#") AS ?pos)
    }
    """
    qres = graph.query(query)
    employees = []
    for row in qres:
        # Если name пустой, берем ID из ссылки (как запасной вариант)
        display_name = str(row.name) if row.name else str(row.emp).split('#')[-1]
        
        employees.append({
            "name": display_name,
            "position": str(row.pos) if row.pos else "Должность не указана"
        })
    return render_template('employees.html', employees=employees)

@app.route('/workload', methods=['POST', 'GET'])
def get_workload():
    query = """
    PREFIX ns: <http://www.semanticweb.org/xe/ontologies/2025/10/untitled-ontology-4#>
    SELECT DISTINCT ?empName ?projectName ?task ?taskName
    WHERE {
        ?emp rdf:type ns:Employee .
        ?emp ns:hasName ?empName .
        
        ?emp ns:Выполняет_назначение ?assign .
        
        ?task ns:Назначена_в ?assign .

        OPTIONAL { ?task ns:hasName ?taskName . }
        
        ?taskSet ns:Содержит_задачи ?task .
        
        ?project ns:Включает_наборы ?taskSet .
        ?project ns:hasName ?projectName .
    }
    ORDER BY ?empName ?projectName
    """
    qres = graph.query(query)
    workload = []
    for row in qres:
        # Если у задачи нет свойства hasName, берем её ID из ссылки
        t_name = str(row.taskName) if row.taskName else str(row.task).split('#')[-1]
        
        workload.append({
            "employee": str(row.empName),
            "project": str(row.projectName),
            "task": t_name
        })
    return render_template('workload.html', workload=workload)

@app.route('/project_tree/<project_id>')
def project_tree(project_id):
    query = f"""
    PREFIX ns: <http://www.semanticweb.org/xe/ontologies/2025/10/untitled-ontology-4#>
    SELECT DISTINCT ?projectName ?ts ?tsName ?taskName ?task
    WHERE {{
        BIND(ns:{project_id} AS ?project)
        ?project ns:hasName ?projectName .
        
        ?project ns:Включает_наборы ?ts .
        
        OPTIONAL {{ ?ts ns:hasName ?tsNameProperty . }}
        
        ?ts ns:Содержит_задачи ?task .
        OPTIONAL {{ ?task ns:hasName ?taskName . }}
        
        BIND(COALESCE(?tsNameProperty, STRAFTER(STR(?ts), "#")) AS ?tsName)
    }}
    ORDER BY ?tsName
    """
    qres = graph.query(query)
    
    tree_data = {}
    project_name = "Проект"
    
    for row in qres:
        project_name = str(row.projectName)
        ts_display = str(row.tsName)
        task_display = str(row.taskName) if row.taskName else str(row.task).split('#')[-1]
        
        if ts_display not in tree_data:
            tree_data[ts_display] = []
        tree_data[ts_display].append(task_display)
            
    return render_template('project_tree.html', project_name=project_name, tree=tree_data)

if __name__ == '__main__':
    app.run(debug=True)