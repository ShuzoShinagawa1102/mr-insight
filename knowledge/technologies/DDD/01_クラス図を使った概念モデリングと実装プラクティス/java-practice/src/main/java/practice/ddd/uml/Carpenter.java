package practice.ddd.uml;

final class Carpenter {
  private final String name;

  Carpenter(String name) {
    this.name = name;
  }

  Board cut(Wood wood, Saw saw) {
    String processed = saw.cut(wood.type());
    return new Board(name + " processed " + processed);
  }
}

