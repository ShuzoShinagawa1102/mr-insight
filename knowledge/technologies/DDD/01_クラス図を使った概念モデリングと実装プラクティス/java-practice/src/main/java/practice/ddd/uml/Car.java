package practice.ddd.uml;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

final class Car {
  private static final AtomicInteger tireSerialSequence = new AtomicInteger(1);

  private final CarSerialNumber serialNumber;
  private final List<Tire> tires;
  private boolean burned;

  private Car(CarSerialNumber serialNumber, List<Tire> tires) {
    this.serialNumber = serialNumber;
    this.tires = new ArrayList<>(tires);
  }

  static Car withFourTires(CarSerialNumber serialNumber, TireSpec tireSpec) {
    List<Tire> tires = new ArrayList<>();
    for (int index = 0; index < 4; index++) {
      String tireSerial = "tire-" + tireSerialSequence.getAndIncrement();
      tires.add(new Tire(new TireSerialNumber(tireSerial), tireSpec));
    }
    return new Car(serialNumber, tires);
  }

  List<Tire> tires() {
    return Collections.unmodifiableList(tires);
  }

  void burn() {
    burned = true;
    for (Tire tire : tires) {
      tire.burn();
    }
  }

  String describe() {
    return "Car{serialNumber="
        + serialNumber.value()
        + ", tires="
        + tires.stream().map(Tire::describe).toList()
        + ", burned="
        + burned
        + "}";
  }
}

