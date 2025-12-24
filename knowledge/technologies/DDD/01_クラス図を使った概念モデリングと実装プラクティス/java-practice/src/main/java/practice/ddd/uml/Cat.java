package practice.ddd.uml;

final class Cat extends Mammal {
  Cat(MammalId id, BodyTemperature bodyTemperature) {
    super(id, bodyTemperature);
  }

  @Override
  String kind() {
    return "Cat";
  }

  @Override
  String voice() {
    return "Meow";
  }
}

