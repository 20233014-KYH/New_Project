package com.inventory.controller;

import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/categories")
public class CategoryController {

    record Category(int id, String name, String desc, String when) {}

    private static final List<Category> CATEGORIES = List.of(
        new Category(1, "기획·작업 방식",   "Claude가 일하는 순서와 계획을 정해 줘요",    "Claude가 매번 제멋대로 일해서 순서와 규칙을 잡고 싶을 때"),
        new Category(2, "토큰·컨텍스트",    "토큰을 아끼고 맥락을 이어 줘요",             "토큰이 너무 빨리 줄거나, 대화가 길어져 앞 내용을 잊을 때"),
        new Category(3, "코드 이해·검색",   "코드와 기술 문서를 찾고 이해하게 도와줘요",   "큰 프로젝트에서 코드나 라이브러리 문서를 잘 찾게 하고 싶을 때"),
        new Category(4, "디자인·프론트엔드","화면을 만들고 다듬어 줘요",                  "화면을 만들거나 디자인 품질을 높이고 싶을 때"),
        new Category(5, "백엔드·인프라",    "서버·DB·클라우드 작업을 도와줘요",           "DB나 서버, 클라우드 작업을 Claude에게 시키고 싶을 때"),
        new Category(6, "QA·테스트",        "테스트·리뷰·보안을 점검해 줘요",             "테스트와 코드 리뷰, 보안 점검을 빠뜨리지 않고 싶을 때")
    );

    @GetMapping
    public List<Category> list() {
        return CATEGORIES;
    }
}
