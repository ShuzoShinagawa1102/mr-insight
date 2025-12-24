package practice.ddd.uml;

import java.util.List;

final class Demos {
  static void abstractionAndGeneralization() {
    List<Mammal> mammals =
        List.of(
            new Human(new MammalId("m-001"), BodyTemperature.celsius(36.5)),
            new Dog(new MammalId("m-002"), BodyTemperature.celsius(38.5)),
            new Cat(new MammalId("m-003"), BodyTemperature.celsius(38.0)));

    for (Mammal mammal : mammals) {
      System.out.println(mammal.describe());
      mammal.walk();
    }
  }

  static void structuringRelationships() {
    // 関連（会社が社員を雇用する）
    Company company = new Company(new CompanyId("c-001"), "ACME");
    Employee alice = new Employee(new EmployeeId("e-001"), "Alice");
    Employee bob = new Employee(new EmployeeId("e-002"), "Bob");
    company.hire(alice);
    company.hire(bob);
    System.out.println(company.describe());

    // コンポジション（車がタイヤを"内部生成"して所有する）
    Car car = Car.withFourTires(new CarSerialNumber("car-100"), TireSpec.standard());
    System.out.println(car.describe());
    car.burn();
    System.out.println("car burned -> " + car.describe());

    // 依存（大工がノコギリを使う）
    Carpenter carpenter = new Carpenter("Taro");
    Saw saw = new Saw("Z-SAW");
    Board board = carpenter.cut(new Wood("oak"), saw);
    System.out.println("dependency -> " + board.describe());
  }

  static void realization() {
    Vehicle car = new CarVehicle("Prius");
    Vehicle train = new Train("Yamanote");
    car.run();
    train.run();
  }

  static void identityAndEquivalence() {
    Customer customerA1 = new Customer(new CustomerId("cust-001"), "A-san");
    Customer customerA2 = new Customer(new CustomerId("cust-001"), "A-san (renamed)");
    System.out.println("entity identity (same id): " + customerA1.sameIdentityAs(customerA2));

    Money yen1000a = Money.yen(1000);
    Money yen1000b = Money.yen(1000);
    System.out.println("value equivalence (same value): " + yen1000a.equals(yen1000b));
  }

  private Demos() {}
}

