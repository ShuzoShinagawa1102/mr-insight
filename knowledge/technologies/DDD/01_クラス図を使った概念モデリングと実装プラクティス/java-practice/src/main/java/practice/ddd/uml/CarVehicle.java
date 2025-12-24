package practice.ddd.uml;

final class CarVehicle implements Vehicle {
  private final String name;

  CarVehicle(String name) {
    this.name = name;
  }

  @Override
  public void run() {
    System.out.println("Car runs: " + name);
  }
}

