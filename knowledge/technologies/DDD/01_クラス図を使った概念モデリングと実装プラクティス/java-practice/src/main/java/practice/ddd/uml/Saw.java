package practice.ddd.uml;

final class Saw {
  private final String model;

  Saw(String model) {
    this.model = model;
  }

  String cut(String woodType) {
    return model + " cut(" + woodType + ")";
  }
}

