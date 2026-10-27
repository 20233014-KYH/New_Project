package com.inventory;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = "inventory.data-dir=../sample-data")
class ApiWebTest {

    @Autowired
    MockMvc mvc;

    @Test
    void categories_returns_6() throws Exception {
        mvc.perform(get("/api/categories"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", hasSize(6)));
    }

    @Test
    void judgments_unknownPair_returns404() throws Exception {
        // superpowers × caveman 은 compat.json에 없음 → 404
        mvc.perform(get("/api/judgments").param("a", "superpowers").param("b", "caveman"))
            .andExpect(status().isNotFound());
    }

    @Test
    void judgments_knownPair_returns200() throws Exception {
        // superpowers × ecc 는 저장된 판정 있음 → 200
        mvc.perform(get("/api/judgments").param("a", "superpowers").param("b", "ecc"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.relation", is("overlap")));
    }

    @Test
    void tools_unknownId_returns404() throws Exception {
        mvc.perform(get("/api/tools/존재하지않는도구"))
            .andExpect(status().isNotFound());
    }

    @Test
    void tools_list_returns_array() throws Exception {
        mvc.perform(get("/api/tools"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$", not(empty())));
    }
}
