package practice.ddd.uml;

final class Dog extends Mammal {
  Dog(MammalId id, BodyTemperature bodyTemperature) {
    super(id, bodyTemperature);
  }

  @Override
  String kind() {
    return "Dog";
  }

  @Override
  String voice() {
    return "Bowwow";
  }
}

