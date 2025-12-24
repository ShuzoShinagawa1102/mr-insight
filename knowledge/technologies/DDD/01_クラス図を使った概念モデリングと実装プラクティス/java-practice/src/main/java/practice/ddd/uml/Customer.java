package practice.ddd.uml;

final class Customer {
  private final CustomerId id;
  private final String name;

  Customer(CustomerId id, String name) {
    this.id = id;
    this.name = name;
  }

  boolean sameIdentityAs(Customer other) {
    return this.id.equals(other.id);
  }

  CustomerId id() {
    return id;
  }

  String name() {
    return name;
  }
}

