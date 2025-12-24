package practice.ddd.uml;

record Board(String description) {
  String describe() {
    return "Board{description=" + description + "}";
  }
}

