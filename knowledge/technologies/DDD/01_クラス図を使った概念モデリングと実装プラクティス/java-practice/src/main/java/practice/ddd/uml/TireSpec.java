package practice.ddd.uml;

record TireSpec(String code) {
  static TireSpec standard() {
    return new TireSpec("STD");
  }
}

