#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MBSE (Model-Based Systems Engineering) Tool
Model-Based Systems Engineering Tool

Provides system modeling, requirements analysis, architecture design and validation functions
"""

import json
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from enum import Enum


class DiagramType(Enum):
    """Supported diagram types"""
    USE_CASE = "use_case"
    CLASS = "class"
    SEQUENCE = "sequence"
    ACTIVITY = "activity"
    STATE_MACHINE = "state_machine"
    COMPONENT = "component"
    DEPLOYMENT = "deployment"


class ArchitectureType(Enum):
    """Architecture types"""
    LAYERED = "layered"
    MICROSERVICES = "microservices"
    MONOLITHIC = "monolithic"
    EVENT_DRIVEN = "event_driven"
    CLEAN_ARCHITECTURE = "clean_architecture"


@dataclass
class Requirement:
    """Requirement class"""
    id: str
    title: str
    description: str
    type: str  # functional, non_functional, constraint
    priority: str  # high, medium, low
    parent_id: Optional[str] = None
    status: str = "draft"  # draft, approved, implemented, verified
    testable: bool = True
    trace_to: List[str] = None  # Trace to other requirements
    
    def __post_init__(self):
        if self.trace_to is None:
            self.trace_to = []


@dataclass
class SystemComponent:
    """System component class"""
    id: str
    name: str
    type: str
    description: str
    interfaces: List[str] = None
    dependencies: List[str] = None
    responsibilities: List[str] = None
    
    def __post_init__(self):
        if self.interfaces is None:
            self.interfaces = []
        if self.dependencies is None:
            self.dependencies = []
        if self.responsibilities is None:
            self.responsibilities = []


class MBSEProject:
    """MBSE Project class"""
    
    def __init__(self, name: str):
        self.name = name
        self.requirements: Dict[str, Requirement] = {}
        self.components: Dict[str, SystemComponent] = {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def add_requirement(self, requirement: Requirement):
        """Add requirement"""
        self.requirements[requirement.id] = requirement
        self.updated_at = datetime.now().isoformat()
    
    def add_component(self, component: SystemComponent):
        """Add component"""
        self.components[component.id] = component
        self.updated_at = datetime.now().isoformat()
    
    def generate_requirements_traceability_matrix(self) -> List[Dict]:
        """Generate requirements traceability matrix"""
        matrix = []
        for req_id, req in self.requirements.items():
            row = {
                "requirement_id": req_id,
                "title": req.title,
                "type": req.type,
                "priority": req.priority,
                "status": req.status,
                "testable": req.testable,
                "parent_requirement": req.parent_id,
                "child_requirements": [],
                "traced_to": req.trace_to,
                "components": []
            }
            
            # Find child requirements
            for child_id, child_req in self.requirements.items():
                if child_req.parent_id == req_id:
                    row["child_requirements"].append(child_id)
            
            # Find related components
            for comp_id, comp in self.components.items():
                if any(resp.lower() in req.description.lower() or 
                      req.title.lower() in resp.lower() 
                      for resp in comp.responsibilities):
                    row["components"].append(comp_id)
            
            matrix.append(row)
        
        return matrix
    
    def analyze_requirements(self) -> Dict[str, Any]:
        """Analyze requirements"""
        analysis = {
            "total_requirements": len(self.requirements),
            "by_type": {},
            "by_priority": {},
            "by_status": {},
            "testable_count": 0,
            "hierarchy_depth": 0,
            "orphaned_requirements": [],
            "circular_dependencies": []
        }
        
        # Count by type
        for req in self.requirements.values():
            req_type = req.type
            analysis["by_type"][req_type] = analysis["by_type"].get(req_type, 0) + 1
            
            priority = req.priority
            analysis["by_priority"][priority] = analysis["by_priority"].get(priority, 0) + 1
            
            status = req.status
            analysis["by_status"][status] = analysis["by_status"].get(status, 0) + 1
            
            if req.testable:
                analysis["testable_count"] += 1
        
        # Find orphaned requirements (no parent and no children)
        for req_id, req in self.requirements.items():
            has_parent = any(child.parent_id == req_id for child in self.requirements.values())
            has_children = req.parent_id is not None
            
            if not has_parent and not has_children:
                analysis["orphaned_requirements"].append(req_id)
        
        # Calculate hierarchy depth
        max_depth = 0
        for req in self.requirements.values():
            depth = 0
            current = req
            while current.parent_id:
                depth += 1
                current = self.requirements.get(current.parent_id)
                if not current:
                    break
            max_depth = max(max_depth, depth)
        
        analysis["hierarchy_depth"] = max_depth
        
        return analysis
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "requirements": {k: asdict(v) for k, v in self.requirements.items()},
            "components": {k: asdict(v) for k, v in self.components.items()}
        }
    
    def save_to_file(self, filename: str):
        """Save to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'MBSEProject':
        """Load from file"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        project = cls(data["name"])
        project.created_at = data["created_at"]
        project.updated_at = data["updated_at"]
        
        # Load requirements
        for req_id, req_data in data["requirements"].items():
            req = Requirement(**req_data)
            project.add_requirement(req)
        
        # Load components
        for comp_id, comp_data in data["components"].items():
            comp = SystemComponent(**comp_data)
            project.add_component(comp)
        
        return project


class SysMLDiagramGenerator:
    """SysML diagram generator"""
    
    @staticmethod
    def generate_use_case_diagram(project: MBSEProject, output_file: str):
        """Generate use case diagram"""
        content = f"""@startuml
title {project.name} - Use Case Diagram

' Define actors
"""
        
        # Extract actors (based on roles in requirements)
        actors = set()
        for req in project.requirements.values():
            if "user" in req.description.lower():
                actors.add("User")
            if "admin" in req.description.lower():
                actors.add("Administrator")
            if "system" in req.description.lower():
                actors.add("External System")
        
        for actor in actors:
            content += f"actor {actor}\n"
        
        content += "\n' Define use cases\n"
        
        # Extract use cases (based on functional requirements)
        for req in project.requirements.values():
            if req.type == "functional":
                content += f'usecase "{req.title}" as UC_{req.id.replace("-", "_")}\n'
        
        content += "\n' Define relationships\n"
        
        # Establish relationships
        for actor in actors:
            for req in project.requirements.values():
                if req.type == "functional":
                    if actor == "User" and any(keyword in req.description.lower() 
                                            for keyword in ["user", "manage", "operation"]):
                        content += f"User --> UC_{req.id.replace('-', '_')}\n"
                    elif actor == "Administrator" and any(keyword in req.description.lower() 
                                                         for keyword in ["admin", "manage", "config"]):
                        content += f"Administrator --> UC_{req.id.replace('-', '_')}\n"
                    elif actor == "External System" and any(keyword in req.description.lower() 
                                                           for keyword in ["api", "interface", "integration"]):
                        content += f"External System --> UC_{req.id.replace('-', '_')}\n"
        
        content += "\n@enduml"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Use case diagram generated: {output_file}")
    
    @staticmethod
    def generate_class_diagram(project: MBSEProject, output_file: str):
        """Generate class diagram"""
        content = f"""@startuml
title {project.name} - Class Diagram

' Define classes
"""
        
        # Generate classes based on components
        for comp_id, comp in project.components.items():
            content += f'class {comp.name} {{\n'
            content += f'  +id: {comp.type}\n'
            content += f'  +description: String\n'
            
            # Add interface methods
            for interface in comp.interfaces:
                content += f'  +{interface}()\n'
            
            content += '}\n\n'
        
        # Define relationships
        for comp in project.components.values():
            for dep in comp.dependencies:
                if dep in [c.name for c in project.components.values()]:
                    content += f"{comp.name} --> {dep}\n"
        
        content += "\n@enduml"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Class diagram generated: {output_file}")
    
    @staticmethod
    def generate_sequence_diagram(project: MBSEProject, output_file: str):
        """Generate sequence diagram"""
        content = f"""@startuml
title {project.name} - Sequence Diagram

' Define participants
"""
        
        # Generate participants based on components
        for comp in project.components.values():
            content += f"participant {comp.name}\n"
        
        content += "\n' Define interaction sequence\n"
        
        # Simple interaction sequence (based on component dependencies)
        for comp in project.components.values():
            for dep_name in comp.dependencies:
                dep_comp = next((c for c in project.components.values() if c.name == dep_name), None)
                if dep_comp:
                    content += f"{comp.name} -> {dep_name}: {comp.responsibilities[0] if comp.responsibilities else 'request'}\n"
                    content += f"{dep_name} --> {comp.name}: response\n"
        
        content += "\n@enduml"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Sequence diagram generated: {output_file}")


class ArchitectureDesigner:
    """Architecture designer"""
    
    @staticmethod
    def design_layered_architecture(project: MBSEProject, output_file: str):
        """Design layered architecture"""
        content = f"""# {project.name} - Layered Architecture Design

## Architecture Overview
Adopting classic layered architecture pattern, dividing system into presentation layer, business logic layer, and data access layer.

## Architecture Layers

### 1. Presentation Layer
- **Responsibility**: User interface display, user interaction handling
- **Components**: 
"""
        
        # Categorize components into different layers
        presentation_components = []
        business_components = []
        data_components = []
        
        for comp in project.components.values():
            if any(keyword in comp.type.lower() for keyword in ["ui", "view", "interface", "web"]):
                presentation_components.append(comp)
            elif any(keyword in comp.type.lower() for keyword in ["service", "business", "logic"]):
                business_components.append(comp)
            elif any(keyword in comp.type.lower() for keyword in ["dao", "repository", "database", "data"]):
                data_components.append(comp)
            else:
                business_components.append(comp)
        
        for comp in presentation_components:
            content += f"  - {comp.name}: {comp.description}\n"
        
        content += """
### 2. Business Logic Layer
- **Responsibility**: Business rule processing, business process control
- **Components**:
"""
        
        for comp in business_components:
            content += f"  - {comp.name}: {comp.description}\n"
        
        content += """
### 3. Data Access Layer
- **Responsibility**: Data persistence, data access control
- **Components**:
"""
        
        for comp in data_components:
            content += f"  - {comp.name}: {comp.description}\n"
        
        content += """
## Inter-layer Dependencies
- Presentation Layer → Business Logic Layer
- Business Logic Layer → Data Access Layer
- Avoid direct dependencies between same layer

## Technology Stack Recommendations
- **Presentation Layer**: React/Vue.js, HTML5, CSS3, JavaScript
- **Business Logic Layer**: Spring Boot, .NET Core, Node.js
- **Data Access Layer**: MyBatis, Entity Framework, Sequelize

## Deployment Architecture
```
[Load Balancer]
    ↓
[Web Server Cluster] ← Presentation Layer
    ↓
[Application Server Cluster] ← Business Logic Layer
    ↓
[Database Cluster] ← Data Access Layer
```
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Layered architecture design generated: {output_file}")
    
    @staticmethod
    def design_microservices_architecture(project: MBSEProject, output_file: str):
        """Design microservices architecture"""
        content = f"""# {project.name} - Microservices Architecture Design

## Architecture Overview
Adopting microservices architecture pattern, dividing system into independent business services, each service responsible for specific business functions.

## Microservices Division

"""
        
        # Generate microservices based on components
        for comp in project.components.values():
            content += f"""### {comp.name} Service
- **Service ID**: {comp.id}
- **Service Type**: {comp.type}
- **Main Responsibilities**: 
"""
            for resp in comp.responsibilities:
                content += f"  - {resp}\n"
            
            content += f"- **Interfaces**: \n"
            for interface in comp.interfaces:
                content += f"  - {interface}\n"
            
            content += f"- **Dependent Services**: {', '.join(comp.dependencies) if comp.dependencies else 'None'}\n\n"
        
        content += """## Inter-service Communication

### Synchronous Communication
- **HTTP/REST API**: Used for queries and simple business operations
- **gRPC**: Used for high-performance internal service communication

### Asynchronous Communication
- **Message Queue**: RabbitMQ, Apache Kafka
- **Event-driven**: Used for decoupling between services

## Data Management
- **Database**: Each service has its own database
- **Data Consistency**: Adopt eventual consistency pattern
- **Distributed Transactions**: Use Saga pattern

## Technology Stack
- **Containerization**: Docker, Kubernetes
- **Service Discovery**: Consul, Eureka
- **API Gateway**: Kong, Zuul
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack

## Deployment Architecture
```
[API Gateway]
    ↓
[Service A] [Service B] [Service C] ... [Service N]
    ↓
[Message Queue]
    ↓
[Database A] [Database B] [Database C] ... [Database N]
```
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Microservices architecture design generated: {output_file}")


class MBSEValidator:
    """MBSE model validator"""
    
    @staticmethod
    def validate_project(project: MBSEProject) -> Dict[str, Any]:
        """Validate project model"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }
        
        # Check requirements completeness
        if not project.requirements:
            validation_result["errors"].append("Project has no defined requirements")
            validation_result["is_valid"] = False
        
        # Check requirement ID uniqueness
        req_ids = set()
        for req_id in project.requirements.keys():
            if req_id in req_ids:
                validation_result["errors"].append(f"Duplicate requirement ID: {req_id}")
                validation_result["is_valid"] = False
            req_ids.add(req_id)
        
        # Check component completeness
        if not project.components:
            validation_result["warnings"].append("Project has no defined components")
        
        # Check component ID uniqueness
        comp_ids = set()
        for comp_id in project.components.keys():
            if comp_id in comp_ids:
                validation_result["errors"].append(f"Duplicate component ID: {comp_id}")
                validation_result["is_valid"] = False
            comp_ids.add(comp_id)
        
        # Check requirements testability
        untestable_reqs = []
        for req in project.requirements.values():
            if not req.testable:
                untestable_reqs.append(req.id)
        
        if untestable_reqs:
            validation_result["warnings"].append(f"存在不可测试的需求: {', '.join(untestable_reqs)}")
        
        # Check dependencies
        missing_deps = []
        for comp in project.components.values():
            for dep in comp.dependencies:
                if dep not in [c.name for c in project.components.values()]:
                    missing_deps.append(f"{comp.name} depends on non-existent component: {dep}")
        
        if missing_deps:
            validation_result["errors"].extend(missing_deps)
            validation_result["is_valid"] = False
        
        # Calculate metrics
        validation_result["metrics"] = {
            "requirements_count": len(project.requirements),
            "components_count": len(project.components),
            "testable_requirements_ratio": len([r for r in project.requirements.values() if r.testable]) / max(len(project.requirements), 1),
            "high_priority_requirements": len([r for r in project.requirements.values() if r.priority == "high"]),
            "implemented_requirements": len([r for r in project.requirements.values() if r.status == "implemented"])
        }
        
        return validation_result


def create_sample_project(name: str) -> MBSEProject:
    """Create sample project"""
    project = MBSEProject(name)
    
    # Add sample requirements
    requirements = [
        Requirement("REQ-001", "User Login Function", "Users can login to system using username and password", "functional", "high"),
        Requirement("REQ-002", "Data Query Function", "Users can query data in the system", "functional", "high"),
        Requirement("REQ-003", "System Performance Requirement", "System response time should not exceed 2 seconds", "non_functional", "medium"),
        Requirement("REQ-004", "Data Security Requirement", "User data must be encrypted when stored", "non_functional", "high"),
        Requirement("REQ-005", "User Management Function", "Administrators can manage user accounts", "functional", "medium"),
    ]
    
    for req in requirements:
        project.add_requirement(req)
    
    # Add sample components
    components = [
        SystemComponent("COMP-001", "UserInterface", "Web Interface", "User interface component", 
                       ["login()", "queryData()", "manageUsers()"],
                       ["UserService", "DataService"],
                       ["User interaction handling", "Interface display"]),
        SystemComponent("COMP-002", "UserService", "Business Service", "User management service",
                       ["authenticate()", "manageUser()"],
                       ["DataAccess"],
                       ["User authentication", "User management"]),
        SystemComponent("COMP-003", "DataService", "Business Service", "Data query service",
                       ["queryData()", "storeData()"],
                       ["DataAccess"],
                       ["Data query", "Data storage"]),
        SystemComponent("COMP-004", "DataAccess", "Data Access", "Data access layer",
                       ["save()", "find()", "update()"],
                       [],
                       ["Data persistence", "Data access control"])
    ]
    
    for comp in components:
        project.add_component(comp)
    
    return project


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MBSE Tool - Model-Based Systems Engineering")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create project command
    create_parser = subparsers.add_parser("create-project", help="Create new project")
    create_parser.add_argument("--name", required=True, help="Project name")
    create_parser.add_argument("--sample", action="store_true", help="Create sample project")
    
    # Requirements management command
    req_parser = subparsers.add_parser("requirements", help="Requirements management")
    req_subparsers = req_parser.add_subparsers(dest="req_command")
    
    req_add = req_subparsers.add_parser("add", help="Add requirement")
    req_add.add_argument("--project", required=True, help="Project file path")
    req_add.add_argument("--id", required=True, help="Requirement ID")
    req_add.add_argument("--title", required=True, help="Requirement title")
    req_add.add_argument("--description", required=True, help="Requirement description")
    req_add.add_argument("--type", required=True, choices=["functional", "non_functional", "constraint"], help="Requirement type")
    req_add.add_argument("--priority", required=True, choices=["high", "medium", "low"], help="Priority")
    
    req_analyze = req_subparsers.add_parser("analyze", help="Analyze requirements")
    req_analyze.add_argument("--project", required=True, help="Project file path")
    
    req_trace = req_subparsers.add_parser("trace", help="Generate traceability matrix")
    req_trace.add_argument("--project", required=True, help="Project file path")
    req_trace.add_argument("--output", required=True, help="Output file path")
    
    # System modeling command
    model_parser = subparsers.add_parser("model", help="System modeling")
    model_subparsers = model_parser.add_subparsers(dest="model_command")
    
    model_add = model_subparsers.add_parser("add-component", help="Add component")
    model_add.add_argument("--project", required=True, help="Project file path")
    model_add.add_argument("--id", required=True, help="Component ID")
    model_add.add_argument("--name", required=True, help="Component name")
    model_add.add_argument("--type", required=True, help="Component type")
    model_add.add_argument("--description", required=True, help="Component description")
    
    # Diagram generation command
    diagram_parser = subparsers.add_parser("diagram", help="Generate diagrams")
    diagram_subparsers = diagram_parser.add_subparsers(dest="diagram_command")
    
    diagram_uc = diagram_subparsers.add_parser("use-case", help="Generate use case diagram")
    diagram_uc.add_argument("--project", required=True, help="Project file path")
    diagram_uc.add_argument("--output", required=True, help="Output file path")
    
    diagram_class = diagram_subparsers.add_parser("class", help="Generate class diagram")
    diagram_class.add_argument("--project", required=True, help="Project file path")
    diagram_class.add_argument("--output", required=True, help="Output file path")
    
    diagram_seq = diagram_subparsers.add_parser("sequence", help="Generate sequence diagram")
    diagram_seq.add_argument("--project", required=True, help="Project file path")
    diagram_seq.add_argument("--output", required=True, help="Output file path")
    
    # Architecture design command
    arch_parser = subparsers.add_parser("architecture", help="Architecture design")
    arch_subparsers = arch_parser.add_subparsers(dest="arch_command")
    
    arch_layered = arch_subparsers.add_parser("layered", help="Design layered architecture")
    arch_layered.add_argument("--project", required=True, help="Project file path")
    arch_layered.add_argument("--output", required=True, help="Output file path")
    
    arch_microservices = arch_subparsers.add_parser("microservices", help="Design microservices architecture")
    arch_microservices.add_argument("--project", required=True, help="Project file path")
    arch_microservices.add_argument("--output", required=True, help="Output file path")
    
    # Validation command
    validate_parser = subparsers.add_parser("validate", help="Validate model")
    validate_parser.add_argument("--project", required=True, help="Project file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "create-project":
            if args.sample:
                project = create_sample_project(args.name)
                filename = f"{args.name.replace(' ', '_').lower()}_project.json"
                project.save_to_file(filename)
                print(f"Sample project created: {filename}")
            else:
                project = MBSEProject(args.name)
                filename = f"{args.name.replace(' ', '_').lower()}_project.json"
                project.save_to_file(filename)
                print(f"Empty project created: {filename}")
        
        elif args.command == "requirements":
            if args.req_command == "add":
                project = MBSEProject.load_from_file(args.project)
                req = Requirement(args.id, args.title, args.description, args.type, args.priority)
                project.add_requirement(req)
                project.save_to_file(args.project)
                print(f"Requirement {args.id} added")
            
            elif args.req_command == "analyze":
                project = MBSEProject.load_from_file(args.project)
                analysis = project.analyze_requirements()
                print("\n=== Requirements Analysis Report ===")
                print(f"Total requirements: {analysis['total_requirements']}")
                print(f"By type: {analysis['by_type']}")
                print(f"By priority: {analysis['by_priority']}")
                print(f"By status: {analysis['by_status']}")
                print(f"Testable requirements: {analysis['testable_count']}")
                print(f"Hierarchy depth: {analysis['hierarchy_depth']}")
                if analysis['orphaned_requirements']:
                    print(f"Orphaned requirements: {analysis['orphaned_requirements']}")
            
            elif args.req_command == "trace":
                project = MBSEProject.load_from_file(args.project)
                matrix = project.generate_requirements_traceability_matrix()
                
                # Save as CSV format
                import csv
                with open(args.output, 'w', newline='', encoding='utf-8') as f:
                    if matrix:
                        writer = csv.DictWriter(f, fieldnames=matrix[0].keys())
                        writer.writeheader()
                        writer.writerows(matrix)
                
                print(f"Requirements traceability matrix generated: {args.output}")
        
        elif args.command == "model":
            if args.model_command == "add-component":
                project = MBSEProject.load_from_file(args.project)
                comp = SystemComponent(args.id, args.name, args.type, args.description)
                project.add_component(comp)
                project.save_to_file(args.project)
                print(f"Component {args.id} added")
        
        elif args.command == "diagram":
            project = MBSEProject.load_from_file(args.project)
            
            if args.diagram_command == "use-case":
                SysMLDiagramGenerator.generate_use_case_diagram(project, args.output)
            elif args.diagram_command == "class":
                SysMLDiagramGenerator.generate_class_diagram(project, args.output)
            elif args.diagram_command == "sequence":
                SysMLDiagramGenerator.generate_sequence_diagram(project, args.output)
        
        elif args.command == "architecture":
            project = MBSEProject.load_from_file(args.project)
            
            if args.arch_command == "layered":
                ArchitectureDesigner.design_layered_architecture(project, args.output)
            elif args.arch_command == "microservices":
                ArchitectureDesigner.design_microservices_architecture(project, args.output)
        
        elif args.command == "validate":
            project = MBSEProject.load_from_file(args.project)
            validation = MBSEValidator.validate_project(project)
            
            print("\n=== Model Validation Report ===")
            print(f"Model validity: {'Valid' if validation['is_valid'] else 'Invalid'}")
            
            if validation['errors']:
                print("\nErrors:")
                for error in validation['errors']:
                    print(f"  - {error}")
            
            if validation['warnings']:
                print("\nWarnings:")
                for warning in validation['warnings']:
                    print(f"  - {warning}")
            
            print("\nMetrics:")
            for metric, value in validation['metrics'].items():
                print(f"  - {metric}: {value}")
    
    except FileNotFoundError:
        print(f"Error: File {args.project} does not exist")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()