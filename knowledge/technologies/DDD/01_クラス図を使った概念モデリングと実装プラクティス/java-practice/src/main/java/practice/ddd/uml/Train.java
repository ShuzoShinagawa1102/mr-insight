package practice.ddd.uml;

final class Train implements Vehicle {
  private final String name;

  Train(String name) {
    this.name = name;
  }

  @Override
  public void run() {
    System.out.println("Train runs: " + name);
  }
}

