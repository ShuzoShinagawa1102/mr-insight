package practice.ddd.uml;

import java.math.BigDecimal;

record Money(String currency, BigDecimal amount) {
  static Money yen(long amount) {
    return new Money("JPY", BigDecimal.valueOf(amount));
  }
}

