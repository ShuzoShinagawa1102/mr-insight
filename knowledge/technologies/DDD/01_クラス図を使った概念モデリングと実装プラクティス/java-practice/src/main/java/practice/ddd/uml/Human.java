package practice.ddd.uml;

final class Human extends Mammal {
  Human(MammalId id, BodyTemperature bodyTemperature) {
    super(id, bodyTemperature);
  }

  @Override
  String kind() {
    return "Human";
  }

  @Override
  String voice() {
    return "Hello";
  }
}

