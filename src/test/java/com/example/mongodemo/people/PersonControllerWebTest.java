package com.example.mongodemo.people;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(PersonController.class)
class PersonControllerWebTest {
  @Autowired private MockMvc mvc;

  @MockBean private PersonRepository repo;

  @Test
  void listReturns200() throws Exception {
    when(repo.findAll()).thenReturn(List.of());
    mvc.perform(get("/api/people")).andExpect(status().isOk());
  }
}

