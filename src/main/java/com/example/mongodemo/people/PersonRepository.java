package com.example.mongodemo.people;

import java.util.Optional;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface PersonRepository extends MongoRepository<Person, String> {
  Optional<Person> findByEmail(String email);
  boolean existsByEmail(String email);
}

