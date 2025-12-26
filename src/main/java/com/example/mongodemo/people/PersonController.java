package com.example.mongodemo.people;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/people")
public class PersonController {
  private final PersonRepository repo;

  public PersonController(PersonRepository repo) {
    this.repo = repo;
  }

  @GetMapping
  public List<Person> list() {
    return repo.findAll();
  }

  @GetMapping("/{id}")
  public ResponseEntity<?> get(@PathVariable String id) {
    return repo.findById(id)
        .<ResponseEntity<?>>map(ResponseEntity::ok)
        .orElseGet(() -> ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "not found")));
  }

  @PostMapping
  public ResponseEntity<?> create(@Valid @RequestBody Person body) {
    // Ignore client-provided id
    body.setId(null);
    try {
      Person saved = repo.save(body);
      return ResponseEntity.status(HttpStatus.CREATED).body(saved);
    } catch (DuplicateKeyException e) {
      return ResponseEntity.status(HttpStatus.CONFLICT)
          .body(Map.of("message", "email already exists", "field", "email"));
    }
  }

  @PutMapping("/{id}")
  public ResponseEntity<?> update(@PathVariable String id, @Valid @RequestBody Person body) {
    Optional<Person> existingOpt = repo.findById(id);
    if (existingOpt.isEmpty()) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "not found"));
    }

    Person existing = existingOpt.get();
    existing.setName(body.getName());
    existing.setEmail(body.getEmail());
    existing.setAge(body.getAge());

    try {
      Person saved = repo.save(existing);
      return ResponseEntity.ok(saved);
    } catch (DuplicateKeyException e) {
      return ResponseEntity.status(HttpStatus.CONFLICT)
          .body(Map.of("message", "email already exists", "field", "email"));
    }
  }

  @DeleteMapping("/{id}")
  public ResponseEntity<?> delete(@PathVariable String id) {
    if (!repo.existsById(id)) {
      return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "not found"));
    }
    repo.deleteById(id);
    return ResponseEntity.noContent().build();
  }
}

