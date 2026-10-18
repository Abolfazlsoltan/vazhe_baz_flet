import unittest
import main
class PersianWordTests(unittest.TestCase):
 def test_alef_madda_is_guessable(self): self.assertIn("آ",main.ALPHABET)
 def test_halfspace_is_not_a_slot(self): self.assertEqual(main.display_chars("رنگین‌کمان"),list("رنگینکمان"))
 def test_mistake_limit_uses_word_length(self): self.assertEqual(len(main.display_chars("سیب")),3); self.assertEqual(len(main.display_chars("آفتابگردان")),10)
 def test_arabic_letter_variants(self): self.assertEqual(main.norm("ك"),"ک"); self.assertEqual(main.norm("ي"),"ی")
if __name__=="__main__": unittest.main()
