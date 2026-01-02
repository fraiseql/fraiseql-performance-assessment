package com.fraiseql;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.graphql.GraphQlAutoConfiguration;

@SpringBootApplication(exclude = {
    GraphQlAutoConfiguration.class  // Disable GraphQL for REST-only implementation
})
public class FraiseqlApplication {

    public static void main(String[] args) {
        SpringApplication.run(FraiseqlApplication.class, args);
    }
}