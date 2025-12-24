package practice.ddd.uml;

abstract class Mammal {
  private final MammalId id;
  private final BodyTemperature bodyTemperature;

  protected Mammal(MammalId id, BodyTemperature bodyTemperature) {
    this.id = id;
    this.bodyTemperature = bodyTemperature;
  }

  final MammalId id() {
    return id;
  }

  final BodyTemperature bodyTemperature() {
    return bodyTemperature;
  }

  abstract String kind();

  abstract String voice();

  final void walk() {
    System.out.println(kind() + " walks. voice=" + voice());
  }

  final String describe() {
    return "Mammal{id=" + id.value() + ", kind=" + kind() + ", bodyTemperature=" + bodyTemperature + "}";
  }
}

