package practice.ddd.uml;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

final class Company {
  private final CompanyId id;
  private final String name;
  private final List<Employee> employees = new ArrayList<>();

  Company(CompanyId id, String name) {
    this.id = id;
    this.name = name;
  }

  void hire(Employee employee) {
    employees.add(employee);
  }

  List<Employee> employees() {
    return Collections.unmodifiableList(employees);
  }

  String describe() {
    return "Company{id="
        + id.value()
        + ", name="
        + name
        + ", employees="
        + employees.stream().map(Employee::name).toList()
        + "}";
  }
}

