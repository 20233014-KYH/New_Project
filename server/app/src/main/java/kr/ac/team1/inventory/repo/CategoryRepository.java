package kr.ac.team1.inventory.repo;

import kr.ac.team1.inventory.domain.Category;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CategoryRepository extends JpaRepository<Category, Integer> {
}
