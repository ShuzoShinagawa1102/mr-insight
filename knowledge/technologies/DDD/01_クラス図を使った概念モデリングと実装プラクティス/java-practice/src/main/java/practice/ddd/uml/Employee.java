package practice.ddd.uml;

final class Employee {
  private final EmployeeId id;
  private final String name;

  Employee(EmployeeId id, String name) {
    this.id = id;
    this.name = name;
  }

  EmployeeId id() {
    return id;
  }

  String name() {
    return name;
  }
}

